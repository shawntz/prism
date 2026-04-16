detrend_runs <- function(subject_ids) {
  pupil_col <- "pupil_raw_deblink_detransient_interpolate_lpfilt"
  pad_n <- 416 + 1000 + 5000 + 4000 # 416ms trigger + 1s post-trigger + 5s stim period + 4s prestim ITI
  runs <- c("01", "02", "03")

  process_run <- function(sub, run) {
    block_name <- paste0("block_", as.integer(run))
    beh_file <- glue("data/raw/{sub}/ses-ret/beh/{sub}_ses-ret_task-clamp_run-{run}_beh.csv")
    eye_file <- glue("data/interim/{sub}/ses-ret/eye/{sub}_ses-ret_task-clamp_run-{run}_desc-eyeris_preproc_epoched.RDS")

    if (!file.exists(beh_file) || !file.exists(eye_file)) {
      return(NULL)
    }

    dat <- read_csv(beh_file, show_col_types = FALSE)
    eye <- read_rds(eye_file)

    if (is.null(eye$epoch_fixprestim[[block_name]])) {
      return(NULL)
    }

    epochs <- bind_rows(
      eye$epoch_fixprestim[[block_name]] |> mutate(epoch = "fixprestim"),
      eye$epoch_realtime1[[block_name]] |> mutate(epoch = "realtime1"),
      eye$epoch_realtime2[[block_name]] |> mutate(epoch = "realtime2")
    ) %>%
      select(STIM, epoch, time_orig, all_of(pupil_col)) %>%
      arrange(STIM, time_orig)

    epochs <- epochs %>%
      group_by(STIM) %>%
      mutate(
        time_gap = c(0, diff(time_orig)) > 10,
        stim_occurrence = cumsum(time_gap) + 1
      ) %>%
      ungroup() %>%
      select(-time_gap)

    stim_order <- dat %>%
      mutate(trial = row_number()) %>%
      select(trial, stim_file, burn_in_trial) %>%
      group_by(stim_file) %>%
      mutate(stim_occurrence = row_number()) %>%
      ungroup()

    ts <- stim_order %>%
      left_join(epochs, by = c("stim_file" = "STIM", "stim_occurrence")) %>%
      group_by(trial) %>%
      group_modify(~ {
        d <- .x |> filter(epoch %in% c("realtime1", "realtime2"))
        pad <- tibble(
          stim_file = d$stim_file[1],
          burn_in_trial = d$burn_in_trial[1],
          stim_occurrence = d$stim_occurrence[1],
          epoch = NA_character_,
          time_orig = NA_real_,
          !!pupil_col := NA_real_
        ) |> slice(rep(1, pad_n))
        bind_rows(d, pad)
      }) %>%
      ungroup() %>%
      mutate(time = (row_number() - 1) / 1000)

    spline_fit <- lm(
      pupil_raw_deblink_detransient_interpolate_lpfilt ~ splines::ns(time, df = 5),
      data = ts |> filter(
        !is.na(pupil_raw_deblink_detransient_interpolate_lpfilt),
        epoch %in% c("realtime1", "realtime2")
      )
    )

    ts <- ts %>%
      mutate(
        spline_pred = predict(spline_fit, newdata = pick(everything())),
        pupil_detrended = pupil_raw_deblink_detransient_interpolate_lpfilt - spline_pred
      )

    trial_trend <- ts %>%
      filter(epoch %in% c("realtime1", "realtime2")) %>%
      group_by(trial) %>%
      summarise(spline_trend = mean(spline_pred), .groups = "drop")

    # fill trials with no realtime data using spline prediction at their time
    missing_trials <- setdiff(unique(ts$trial), trial_trend$trial)
    if (length(missing_trials) > 0) {
      missing_trends <- ts %>%
        filter(trial %in% missing_trials) %>%
        group_by(trial) %>%
        summarise(spline_trend = first(spline_pred), .groups = "drop")
      trial_trend <- bind_rows(trial_trend, missing_trends)
    }

    df <- dat %>%
      mutate(trial = row_number()) %>%
      filter(!(abort_ret_trial & !burn_in_trial)) %>%
      mutate(
        trigger_window_mean = case_when(
          burn_in_trial == TRUE ~ latest_baseline_mean,
          trigger_window_mean_two != "None" ~ as.numeric(trigger_window_mean_two),
          TRUE ~ as.numeric(trigger_window_mean_one)
        ),
        trigger_status = case_when(
          burn_in_trial & abort_ret_trial ~ "burnin_abort",
          burn_in_trial ~ "burnin",
          TRUE ~ paste(
            if_else(trigger_should_launch, "lapse", "nolapse"),
            if_else(trigger_actually_delivered, "trigger", "notrigger"),
            sep = "_"
          )
        )
      ) %>%
      left_join(trial_trend, by = "trial") %>%
      mutate(
        trigger_window_mean_detrended = trigger_window_mean - spline_trend,
        trigger_baseline_mean_detrended = trigger_baseline_mean - spline_trend
      )

    realtime_detrended <- ts %>% filter(epoch %in% c("realtime1", "realtime2"))
    global_baseline_mean <- mean(realtime_detrended$pupil_detrended, na.rm = TRUE)
    global_baseline_sd <- sd(realtime_detrended$pupil_detrended, na.rm = TRUE)
    global_lower <- global_baseline_mean - global_baseline_sd
    global_upper <- global_baseline_mean + global_baseline_sd

    df <- df %>%
      mutate(
        detrended_should_launch = trigger_window_mean_detrended < global_lower |
          trigger_window_mean_detrended > global_upper,
        detrended_status = case_when(
          burn_in_trial & abort_ret_trial ~ "burnin_abort",
          burn_in_trial ~ "burnin",
          TRUE ~ paste(
            if_else(detrended_should_launch, "lapse", "nolapse"),
            if_else(trigger_actually_delivered, "trigger", "notrigger"),
            sep = "_"
          )
        ),
        transition = case_when(
          burn_in_trial & abort_ret_trial ~ "burnin_abort",
          burn_in_trial ~ "burnin",
          TRUE ~ paste(trigger_status, detrended_status, sep = " > ")
        )
      )

    transition_colors <- c(
      "nolapse_notrigger > lapse_notrigger" = "red",
      "nolapse_notrigger > nolapse_notrigger" = "green",
      "lapse_notrigger > lapse_notrigger" = "red",
      "lapse_notrigger > nolapse_notrigger" = "green",
      "lapse_trigger > lapse_trigger" = "red",
      "lapse_trigger > nolapse_trigger" = "green",
      "burnin" = "black",
      "burnin_abort" = "gray"
    )
    transition_shapes <- c(
      "nolapse_notrigger > lapse_notrigger" = 15,
      "nolapse_notrigger > nolapse_notrigger" = 15,
      "lapse_notrigger > lapse_notrigger" = 16,
      "lapse_notrigger > nolapse_notrigger" = 16,
      "lapse_trigger > lapse_trigger" = 17,
      "lapse_trigger > nolapse_trigger" = 17,
      "burnin" = 16,
      "burnin_abort" = 1
    )

    burnin_nan_p1 <- df %>% filter(burn_in_trial, is.nan(trigger_window_mean))
    burnin_nan_p2 <- df %>% filter(burn_in_trial, is.nan(trigger_window_mean_detrended))

    p1 <- ggplot(df, aes(x = prestim_iti_offset, y = trigger_window_mean)) +
      geom_vline(
        data = burnin_nan_p1, aes(xintercept = prestim_iti_offset),
        color = "gray", linewidth = 0.5
      ) +
      geom_point(aes(col = transition, shape = transition), size = 2) +
      scale_color_manual(values = transition_colors) +
      scale_shape_manual(values = transition_shapes) +
      geom_line(aes(y = trigger_baseline_mean), linetype = "dashed") +
      geom_line(aes(y = trigger_lower_threshold), linetype = "dotted") +
      geom_line(aes(y = trigger_upper_threshold), linetype = "dotted") +
      geom_line(aes(y = spline_trend), color = "red", linewidth = 1) +
      theme_classic(base_size = 10) +
      theme(
        legend.position = "bottom",
        legend.text = element_text(size = 6),
        legend.title = element_text(size = 7),
        legend.key.size = unit(0.4, "lines"),
        legend.spacing.x = unit(0.2, "lines"),
        legend.spacing.y = unit(0.1, "lines"),
        legend.margin = margin(0, 0, 0, 0)
      ) +
      ggtitle(paste(sub, "run", run, "- Original"))

    p2 <- ggplot(df, aes(x = prestim_iti_offset, y = trigger_window_mean_detrended)) +
      geom_vline(
        data = burnin_nan_p2, aes(xintercept = prestim_iti_offset),
        color = "gray", linewidth = 0.5
      ) +
      geom_point(aes(col = transition, shape = transition), size = 2) +
      scale_color_manual(values = transition_colors) +
      scale_shape_manual(values = transition_shapes) +
      geom_hline(yintercept = global_baseline_mean, linetype = "dashed") +
      geom_hline(yintercept = global_lower, linetype = "dotted") +
      geom_hline(yintercept = global_upper, linetype = "dotted") +
      theme_classic(base_size = 10) +
      theme(
        legend.position = "bottom",
        legend.text = element_text(size = 6),
        legend.title = element_text(size = 7),
        legend.key.size = unit(0.4, "lines"),
        legend.spacing.x = unit(0.2, "lines"),
        legend.spacing.y = unit(0.1, "lines"),
        legend.margin = margin(0, 0, 0, 0)
      ) +
      ggtitle(paste(sub, "run", run, "- Detrended"))

    ts_df <- ts %>%
      mutate(subject = sub, run = run)

    trial_df <- df %>%
      mutate(subject = sub, run = run) |>
      mutate(across(everything(), as.character))

    list(p1 = p1, p2 = p2, trial_df = trial_df, ts_df = ts_df)
  }

  all_trial_dfs <- list()

  pdf("reports/detrend_comparison.pdf", width = 11, height = 17)
  for (sub in subject_ids) {
    plots <- list()
    for (run in runs) {
      result <- tryCatch(process_run(sub, run), error = function(e) {
        message(paste("Skipping", sub, "run", run, ":", e$message))
        NULL
      })
      if (!is.null(result)) {
        plots <- c(plots, list(result$p1, result$p2))
        all_trial_dfs <- c(all_trial_dfs, list(result$trial_df))
      }
    }
    if (length(plots) > 0) {
      print(patchwork::wrap_plots(plots, ncol = 2, nrow = 3))
    }
  }
  dev.off()

  all_df <- bind_rows(all_trial_dfs)

  return(all_df)
}
