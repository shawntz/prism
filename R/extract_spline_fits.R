extract_spline_fits <- function(ts_files) {
  map_dfr(ts_files, function(f) {
    ts <- read_rds(f)
    if (nrow(ts) == 0) {
      return(NULL)
    }

    ts %>%
      filter(epoch %in% c("realtime1", "realtime2")) %>%
      group_by(subject, run) %>%
      mutate(run_sample = row_number()) %>%
      filter(run_sample %% 100 == 0) %>%
      select(subject, run, run_sample, time, spline_pred) %>%
      ungroup()
  })
}
