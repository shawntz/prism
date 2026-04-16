avg_spline_by_run <- function(spline_fits) {
  spline_fits %>%
    group_by(run, run_sample) %>%
    summarise(
      mean_spline = mean(spline_pred, na.rm = TRUE),
      sd_spline = sd(spline_pred, na.rm = TRUE),
      n = n(),
      se_spline = sd_spline / sqrt(n),
      .groups = "drop"
    )
}
