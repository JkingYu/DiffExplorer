#!/usr/bin/env Rscript

# ================================================================
# DiffExplorer 统计引擎（三路可选）
# 用法: Rscript run_stats.R <data_path> <params_path> <output_path>
# ================================================================

suppressPackageStartupMessages({
  library(readxl)
  library(writexl)
  library(jsonlite)
  library(dplyr)
  library(tidyr)
  library(car)
  library(DescTools)
  library(agricolae)
  library(FSA)
  library(PMCMRplus)
  library(kSamples)
})

# ---------- 辅助函数 ----------
safe_shapiro <- function(x) {
  if (length(x) >= 3 && length(unique(x)) > 1) {
    res <- shapiro.test(x)
    return(res$p.value)
  } else return(NA_real_)
}

calc_variance_ratio <- function(sub_df) {
  vars <- tapply(sub_df$Value, sub_df$Group, var, na.rm = TRUE)
  if (length(vars) >= 2 && all(!is.na(vars)) && min(vars) > 0) {
    return(max(vars) / min(vars))
  } else return(NA_real_)
}

all_pairs <- function(groups) {
  if (length(groups) < 2) return(list())
  combn(groups, 2, simplify = FALSE)
}

get_pairs <- function(groups, test_name, control, specified_pairs) {
  if (test_name %in% c("Dunnett", "Steel", "Dunnett_T3")) {
    if (is.na(control) || !(control %in% groups)) return(list())
    others <- setdiff(groups, control)
    return(lapply(others, function(g) c(control, g)))
  } else if (test_name == "LSD" && length(specified_pairs) > 0) {
    valid <- sapply(specified_pairs, function(p) all(p %in% groups))
    return(specified_pairs[valid])
  } else {
    return(all_pairs(groups))
  }
}

extract_pairs_from_PMCMR <- function(obj, pairs) {
  stat_mat <- obj$statistic
  p_mat <- obj$p.value
  row_names <- rownames(stat_mat)
  col_names <- colnames(stat_mat)
  pair_map <- list()
  for (pair in pairs) {
    g1 <- pair[1]; g2 <- pair[2]
    stat <- NA; pval <- NA
    if (g1 %in% row_names && g2 %in% col_names) {
      stat <- stat_mat[g1, g2]
      pval <- p_mat[g1, g2]
    } else if (g2 %in% row_names && g1 %in% col_names) {
      stat <- stat_mat[g2, g1]
      pval <- p_mat[g2, g1]
    }
    if (!is.na(stat) && !is.na(pval)) {
      pair_map[[paste(g1, g2, sep = "-")]] <- list(stat = stat, pval = pval)
      pair_map[[paste(g2, g1, sep = "-")]] <- list(stat = -stat, pval = pval)
    }
  }
  return(pair_map)
}

collect_row <- function(result_list, ind, comparison, norm_note, lev_result, var_ratio,
                        test_type, stat, p_val, p_adj, sig, note) {
  result_list[[length(result_list) + 1]] <- data.frame(
    Indicator = ind,
    Comparison = comparison,
    Normality = norm_note,
    Levene_Result = lev_result,
    Variance_Ratio = round(var_ratio, 4),
    Test = test_type,
    Statistic = round(stat, 4),
    P_Value = round(p_val, 6),
    P_Adjusted = round(p_adj, 6),
    Significant = ifelse(is.na(sig), "No", ifelse(sig, "Yes", "No")),
    Note = note,
    stringsAsFactors = FALSE
  )
  return(result_list)
}

# ---------- 主函数 ----------
main <- function(data_path = NULL, params_path = NULL, output_path = NULL) {
  if (is.null(data_path) || is.null(params_path) || is.null(output_path)) {
    args <- commandArgs(trailingOnly = TRUE)
    if (length(args) < 3) stop("Usage: Rscript run_stats.R <data_path> <params_path> <output_path>")
    data_path <- args[1]
    params_path <- args[2]
    output_path <- args[3]
  }
  out_dir <- dirname(output_path)
  if (out_dir == ".") out_dir <- "temp"
  output_path <- file.path(out_dir, "Routput.xlsx")
  
  raw <- read_excel(data_path, col_names = FALSE)
  if (nrow(raw) < 3) stop("Data rows < 3")
  groups <- trimws(as.character(unlist(raw[1, -1])))
  samples <- trimws(as.character(unlist(raw[2, -1])))
  indicators <- trimws(as.character(unlist(raw[3:nrow(raw), 1])))
  mat <- raw[3:nrow(raw), -1]
  colnames(mat) <- samples
  
  long_data <- mat %>%
    mutate(Indicator = indicators) %>%
    pivot_longer(cols = -Indicator, names_to = "Sample", values_to = "Value") %>%
    left_join(data.frame(Sample = samples, Group = groups), by = "Sample") %>%
    select(Indicator, Group, Value) %>%
    mutate(Value = as.numeric(Value), Group = trimws(Group)) %>%
    filter(!is.na(Value))
  
  all_indicators <- unique(long_data$Indicator)
  all_groups <- unique(long_data$Group)
  
  params <- fromJSON(params_path)
  param_posthoc <- params$param_posthoc %||% "SNK"
  welch_posthoc <- params$welch_posthoc %||% "Games_Howell"
  nonparam_posthoc <- params$nonparam_posthoc %||% "Dunn"
  adjust <- params$adjust %||% "BH"
  control <- params$control %||% NA
  specified_pairs <- params$specified_pairs %||% list()
  force_welch <- params$force_welch %||% FALSE
  adjust_lower <- tolower(adjust)
  
  result_rows <- list()
  norm_rows <- list()
  levene_rows <- list()
  
  for (ind in all_indicators) {
    sub_df <- long_data %>% filter(Indicator == ind)
    sub_df <- sub_df %>% group_by(Group) %>% filter(n() >= 2) %>% ungroup()
    valid_groups <- unique(sub_df$Group)
    if (length(valid_groups) < 2) {
      result_rows <- collect_row(result_rows, ind, "Overall", "Insufficient",
                                 NA, NA, "SKIP", NA, NA, NA, FALSE,
                                 "每组样本量不足2")
      norm_row <- data.frame(Indicator = ind)
      for (g in all_groups) norm_row[[g]] <- NA
      norm_rows[[ind]] <- norm_row
      levene_rows[[ind]] <- data.frame(Indicator = ind, Levene_P = NA)
      next
    }
    groups_valid <- valid_groups
    is_multi <- length(groups_valid) > 2
    
    sw_pvals <- sapply(groups_valid, function(g) {
      safe_shapiro(sub_df %>% filter(Group == g) %>% pull(Value))
    })
    is_normal <- all(!is.na(sw_pvals) & sw_pvals > 0.05)
    norm_note <- ifelse(is_normal, "Normal", "Non-normal")
    
    norm_row <- data.frame(Indicator = ind)
    for (g in all_groups) {
      if (g %in% groups_valid) norm_row[[g]] <- sw_pvals[g] else norm_row[[g]] <- NA
    }
    norm_rows[[ind]] <- norm_row
    
    if (is_normal && length(groups_valid) >= 2) {
      lev_p <- tryCatch({
        leveneTest(Value ~ Group, data = sub_df, center = mean)$`Pr(>F)`[1]
      }, error = function(e) NA)
      is_equal <- ifelse(is.na(lev_p), FALSE, lev_p > 0.05)
    } else {
      lev_p <- NA; is_equal <- FALSE
    }
    lev_result <- ifelse(is.na(lev_p), NA, ifelse(is_equal, "Equal", "Unequal"))
    levene_rows[[ind]] <- data.frame(Indicator = ind, Levene_P = round(lev_p, 6))
    var_ratio <- calc_variance_ratio(sub_df)
    
    # ========== 两组比较 ==========
    if (!is_multi) {
      g1 <- groups_valid[1]; g2 <- groups_valid[2]
      d1 <- sub_df %>% filter(Group == g1) %>% pull(Value)
      d2 <- sub_df %>% filter(Group == g2) %>% pull(Value)
      
      if (!is_normal) {
        test <- wilcox.test(d1, d2, exact = FALSE, correct = TRUE)
        result_rows <- collect_row(result_rows, ind, paste(g1, "vs", g2),
                                   norm_note, lev_result, var_ratio,
                                   "Mann-Whitney U", test$statistic, test$p.value, NA,
                                   test$p.value < 0.05, "Non-parametric (MWU)")
      } else if (is_equal) {
        test <- t.test(d1, d2, var.equal = TRUE)
        result_rows <- collect_row(result_rows, ind, paste(g1, "vs", g2),
                                   norm_note, lev_result, var_ratio,
                                   "Student's t", test$statistic, test$p.value, NA,
                                   test$p.value < 0.05, "var.equal=TRUE")
      } else { # 正态但方差不齐
        if (force_welch) {
          test <- t.test(d1, d2, var.equal = FALSE)
          result_rows <- collect_row(result_rows, ind, paste(g1, "vs", g2),
                                     norm_note, lev_result, var_ratio,
                                     "Welch t", test$statistic, test$p.value, NA,
                                     test$p.value < 0.05, "var.equal=FALSE (Welch)")
        } else {
          test <- wilcox.test(d1, d2, exact = FALSE, correct = TRUE)
          result_rows <- collect_row(result_rows, ind, paste(g1, "vs", g2),
                                     norm_note, lev_result, var_ratio,
                                     "Mann-Whitney U", test$statistic, test$p.value, NA,
                                     test$p.value < 0.05, "Non-parametric (MWU) due to unequal variances")
        }
      }
      next
    }
    
    # ========== 多组比较 ==========
    # 路径判定：只有 force_welch=TRUE 且 正态且方差不齐 时才走 Welch 路径
    if (!is_normal) {
      use_kw <- TRUE; use_welch <- FALSE
    } else if (is_normal && is_equal) {
      use_kw <- FALSE; use_welch <- FALSE
    } else { # 正态且方差不齐
      if (force_welch) {
        use_welch <- TRUE; use_kw <- FALSE
      } else {
        use_kw <- TRUE; use_welch <- FALSE
      }
    }
    
    # 获取配对列表（根据最终路径）
    if (use_kw) {
      pairs <- get_pairs(groups_valid, nonparam_posthoc, control, specified_pairs)
      if (length(pairs) == 0) pairs <- all_pairs(groups_valid)
    } else if (use_welch) {
      pairs <- get_pairs(groups_valid, welch_posthoc, control, specified_pairs)
      if (length(pairs) == 0) pairs <- all_pairs(groups_valid)
    } else {
      pairs <- get_pairs(groups_valid, param_posthoc, control, specified_pairs)
      if (length(pairs) == 0) pairs <- all_pairs(groups_valid)
    }
    
    overall_p <- NA; overall_stat <- NA; test_name <- ""
    
    if (use_kw) {
      kw <- kruskal.test(Value ~ Group, data = sub_df)
      overall_p <- kw$p.value; overall_stat <- kw$statistic
      test_name <- "Kruskal-Wallis"
      result_rows <- collect_row(result_rows, ind, "Overall",
                                 norm_note, lev_result, var_ratio,
                                 test_name, overall_stat, overall_p, NA,
                                 overall_p < 0.05, "Non-parametric main test")
      
      if (overall_p < 0.05) {
        if (nonparam_posthoc == "Dunn") {
          dunn <- dunnTest(Value ~ Group, data = sub_df, method = adjust_lower)
          res <- dunn$res
          pair_map <- list()
          for (i in 1:nrow(res)) {
            comp <- res$Comparison[i]
            parts <- strsplit(comp, " - ")[[1]]
            if (length(parts) == 2) {
              g1 <- parts[1]; g2 <- parts[2]
              pair_map[[paste(g1,g2,sep="-")]] <- list(stat=res$Z[i], pval=res$P.adj[i])
              pair_map[[paste(g2,g1,sep="-")]] <- list(stat=res$Z[i], pval=res$P.adj[i])
            }
          }
          for (pair in pairs) {
            key <- paste(pair[1], pair[2], sep="-")
            info <- pair_map[[key]]
            if (!is.null(info)) {
              result_rows <- collect_row(result_rows, ind, paste(pair[1], "vs", pair[2]),
                                         norm_note, lev_result, var_ratio,
                                         paste0("Dunn+", adjust), info$stat, NA, info$pval,
                                         info$pval < 0.05, paste0("Dunn with ", adjust))
            }
          }
        } else if (nonparam_posthoc == "Nemenyi") {
          group_factor <- factor(sub_df$Group)
          group_levels <- levels(group_factor)
          group_num <- as.numeric(group_factor)
          nem <- kwAllPairsNemenyiTest(x = sub_df$Value, g = group_num)
          stat_mat <- nem$statistic; p_mat <- nem$p.value
          pair_map <- list()
          for (i in 1:nrow(stat_mat)) {
            for (j in 1:ncol(stat_mat)) {
              if (!is.na(stat_mat[i,j]) && !is.na(p_mat[i,j])) {
                g1 <- group_levels[as.numeric(rownames(stat_mat)[i])]
                g2 <- group_levels[as.numeric(colnames(stat_mat)[j])]
                if (g1 != g2) {
                  pair_map[[paste(g1,g2,sep="-")]] <- list(stat=stat_mat[i,j], pval=p_mat[i,j])
                  pair_map[[paste(g2,g1,sep="-")]] <- list(stat=stat_mat[i,j], pval=p_mat[i,j])
                }
              }
            }
          }
          for (pair in pairs) {
            key <- paste(pair[1], pair[2], sep="-")
            info <- pair_map[[key]]
            if (!is.null(info)) {
              result_rows <- collect_row(result_rows, ind, paste(pair[1], "vs", pair[2]),
                                         norm_note, lev_result, var_ratio,
                                         "Nemenyi", info$stat, NA, info$pval,
                                         info$pval < 0.05, "Nemenyi (Tukey-Dist)")
            }
          }
        } else if (nonparam_posthoc == "Steel") {
          if (!is.na(control) && control %in% groups_valid) {
            group_list <- list()
            group_list[[control]] <- sub_df %>% filter(Group == control) %>% pull(Value)
            for (g in setdiff(groups_valid, control)) {
              group_list[[g]] <- sub_df %>% filter(Group == g) %>% pull(Value)
            }
            steel <- Steel.test(group_list)
            treat_names <- names(group_list)[-1]
            pair_map <- list()
            for (i in seq_along(treat_names)) {
              treat <- treat_names[i]
              pair_map[[paste(treat, control, sep="-")]] <- list(stat=steel$Wstand[i], pval=steel$pval.asympt.adj[i])
              pair_map[[paste(control, treat, sep="-")]] <- list(stat=steel$Wstand[i], pval=steel$pval.asympt.adj[i])
            }
            for (pair in pairs) {
              g1 <- pair[1]; g2 <- pair[2]
              if (g1 == control || g2 == control) {
                treat <- if (g1 == control) g2 else g1
                key <- paste(treat, control, sep="-")
                info <- pair_map[[key]]
                if (!is.null(info)) {
                  result_rows <- collect_row(result_rows, ind, paste(control, "vs", treat),
                                             norm_note, lev_result, var_ratio,
                                             "Steel", info$stat, NA, info$pval,
                                             info$pval < 0.05, "Steel (nonparametric)")
                }
              }
            }
          }
        }
      }
    } else if (use_welch) {
      welch <- oneway.test(Value ~ Group, data = sub_df, var.equal = FALSE)
      overall_p <- welch$p.value; overall_stat <- welch$statistic
      test_name <- "Welch ANOVA"
      result_rows <- collect_row(result_rows, ind, "Overall",
                                 norm_note, lev_result, var_ratio,
                                 test_name, overall_stat, overall_p, NA,
                                 overall_p < 0.05, paste0("df1,df2:", paste(round(welch$parameter,2), collapse=",")))
      
      if (overall_p < 0.05) {
        if (welch_posthoc == "Games_Howell") {
          sub_df$Group <- factor(sub_df$Group)
          gh <- gamesHowellTest(x = sub_df$Value, g = sub_df$Group)
          pair_map <- extract_pairs_from_PMCMR(gh, pairs)
          for (pair in pairs) {
            key <- paste(pair[1], pair[2], sep="-")
            info <- pair_map[[key]]
            if (!is.null(info)) {
              result_rows <- collect_row(result_rows, ind, paste(pair[1], "vs", pair[2]),
                                         norm_note, lev_result, var_ratio,
                                         "Games-Howell", info$stat, NA, info$pval,
                                         info$pval < 0.05, "Games-Howell (unequal variances)")
            }
          }
        } else if (welch_posthoc == "Dunnett_T3") {
          if (!is.na(control) && control %in% groups_valid) {
            sub_df$Group <- factor(sub_df$Group)
            sub_df$Group <- relevel(sub_df$Group, ref = control)
            t3 <- dunnettT3Test(x = sub_df$Value, g = sub_df$Group, control = control)
            pair_map <- extract_pairs_from_PMCMR(t3, pairs)
            for (pair in pairs) {
              key <- paste(pair[1], pair[2], sep="-")
              info <- pair_map[[key]]
              if (!is.null(info)) {
                result_rows <- collect_row(result_rows, ind, paste(pair[1], "vs", pair[2]),
                                           norm_note, lev_result, var_ratio,
                                           "Dunnett's T3", info$stat, NA, info$pval,
                                           info$pval < 0.05, "Dunnett's T3 (unequal variances)")
              }
            }
          }
        }
      }
    } else {
      aov_res <- aov(Value ~ Group, data = sub_df)
      f_stat <- summary(aov_res)[[1]]$`F value`[1]
      f_p <- summary(aov_res)[[1]]$`Pr(>F)`[1]
      overall_p <- f_p; overall_stat <- f_stat
      test_name <- "ANOVA"
      result_rows <- collect_row(result_rows, ind, "Overall",
                                 norm_note, lev_result, var_ratio,
                                 test_name, overall_stat, overall_p, NA,
                                 overall_p < 0.05, "ANOVA overall")
      
      if (overall_p < 0.05) {
        if (param_posthoc == "LSD") {
          lsd <- LSD.test(aov_res, "Group", p.adj = adjust, group = FALSE)
          comps <- lsd$comparison
          pair_map <- list()
          if (nrow(comps) > 0) {
            for (i in 1:nrow(comps)) {
              pair_name <- rownames(comps)[i]
              parts <- trimws(strsplit(pair_name, "-")[[1]])
              if (length(parts) == 2) {
                g1 <- parts[1]; g2 <- parts[2]
                pair_map[[paste(g1,g2,sep="-")]] <- list(stat=comps[i,"difference"], pval=comps[i,"pvalue"])
                pair_map[[paste(g2,g1,sep="-")]] <- list(stat=comps[i,"difference"], pval=comps[i,"pvalue"])
              }
            }
          }
          for (pair in pairs) {
            key <- paste(pair[1], pair[2], sep="-")
            info <- pair_map[[key]]
            if (!is.null(info)) {
              result_rows <- collect_row(result_rows, ind, paste(pair[1], "vs", pair[2]),
                                         norm_note, lev_result, var_ratio,
                                         paste0("LSD+", adjust), info$stat, NA, info$pval,
                                         info$pval < 0.05, paste0("LSD with ", adjust))
            }
          }
        } else if (param_posthoc == "SNK") {
          snk <- SNK.test(aov_res, "Group", group = FALSE)
          comps <- snk$comparison
          pair_map <- list()
          if (nrow(comps) > 0) {
            for (i in 1:nrow(comps)) {
              pair_name <- rownames(comps)[i]
              parts <- trimws(strsplit(pair_name, "-")[[1]])
              if (length(parts) == 2) {
                g1 <- parts[1]; g2 <- parts[2]
                pair_map[[paste(g1,g2,sep="-")]] <- list(stat=comps[i,"difference"], pval=comps[i,"pvalue"])
                pair_map[[paste(g2,g1,sep="-")]] <- list(stat=comps[i,"difference"], pval=comps[i,"pvalue"])
              }
            }
          }
          for (pair in pairs) {
            key <- paste(pair[1], pair[2], sep="-")
            info <- pair_map[[key]]
            if (!is.null(info)) {
              result_rows <- collect_row(result_rows, ind, paste(pair[1], "vs", pair[2]),
                                         norm_note, lev_result, var_ratio,
                                         "SNK", info$stat, NA, info$pval,
                                         info$pval < 0.05, "Student-Newman-Keuls")
            }
          }
        } else if (param_posthoc == "Tukey") {
          hsd <- HSD.test(aov_res, "Group", group = FALSE)
          comps <- hsd$comparison
          pair_map <- list()
          if (nrow(comps) > 0) {
            for (i in 1:nrow(comps)) {
              pair_name <- rownames(comps)[i]
              parts <- trimws(strsplit(pair_name, "-")[[1]])
              if (length(parts) == 2) {
                g1 <- parts[1]; g2 <- parts[2]
                pair_map[[paste(g1,g2,sep="-")]] <- list(stat=comps[i,"difference"], pval=comps[i,"pvalue"])
                pair_map[[paste(g2,g1,sep="-")]] <- list(stat=comps[i,"difference"], pval=comps[i,"pvalue"])
              }
            }
          }
          for (pair in pairs) {
            key <- paste(pair[1], pair[2], sep="-")
            info <- pair_map[[key]]
            if (!is.null(info)) {
              result_rows <- collect_row(result_rows, ind, paste(pair[1], "vs", pair[2]),
                                         norm_note, lev_result, var_ratio,
                                         "Tukey HSD", info$stat, NA, info$pval,
                                         info$pval < 0.05, "Tukey HSD")
            }
          }
        } else if (param_posthoc == "Dunnett") {
          if (!is.na(control) && control %in% groups_valid) {
            sub_df$Group <- factor(sub_df$Group)
            sub_df$Group <- relevel(sub_df$Group, ref = control)
            dunn <- DunnettTest(Value ~ Group, data = sub_df, control = control)
            mat <- dunn[[control]]
            if (!is.null(mat) && is.matrix(mat) && nrow(mat) > 0) {
              pair_map <- list()
              for (cn in rownames(mat)) {
                parts <- strsplit(cn, "-")[[1]]
                treat <- parts[1]; ctrl <- parts[2]
                pair_map[[paste(treat, ctrl, sep="-")]] <- list(stat=as.numeric(mat[cn,"diff"]), pval=as.numeric(mat[cn,"pval"]))
                pair_map[[paste(ctrl, treat, sep="-")]] <- list(stat=as.numeric(mat[cn,"diff"]), pval=as.numeric(mat[cn,"pval"]))
              }
              for (pair in pairs) {
                g1 <- pair[1]; g2 <- pair[2]
                if (g1 == control || g2 == control) {
                  treat <- if (g1 == control) g2 else g1
                  key <- paste(treat, control, sep="-")
                  info <- pair_map[[key]]
                  if (!is.null(info)) {
                    result_rows <- collect_row(result_rows, ind, paste(control, "vs", treat),
                                               norm_note, lev_result, var_ratio,
                                               "Dunnett", info$stat, NA, info$pval,
                                               info$pval < 0.05, "Dunnett (diff)")
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  
  # 合并输出（精简版）
  norm_df <- do.call(rbind, norm_rows)
  levene_df <- do.call(rbind, levene_rows)
  full_df <- do.call(rbind, result_rows)
  if (nrow(full_df) == 0) {
    final_df <- data.frame()
  } else {
    slim_list <- list()
    for (ind in unique(full_df$Indicator)) {
      sub <- full_df[full_df$Indicator == ind, ]
      overall_row <- sub[sub$Comparison == "Overall", ]
      if (nrow(overall_row) == 0) {
        slim_list[[ind]] <- sub
      } else {
        p_val <- overall_row$P_Value[1]
        if (is.na(p_val) || p_val < 0.05) {
          slim_list[[ind]] <- sub
        } else {
          slim_list[[ind]] <- overall_row
        }
      }
    }
    final_df <- do.call(rbind, slim_list)
    if ("Levene_P" %in% colnames(final_df)) {
      final_df <- final_df[, !(colnames(final_df) == "Levene_P")]
    }
  }
  
  output_sheets <- list(Normality = norm_df, Levene = levene_df, Results = final_df)
  write_xlsx(output_sheets, path = output_path)
  cat("Results saved to:", output_path, "\n")
  cat("Sheets: Normality, Levene, Results\n")
  return(invisible(final_df))
}

if (!interactive()) {
  main()
}