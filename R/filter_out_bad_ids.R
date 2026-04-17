filter_out_bad_ids <- function(file, df) {
  good_ids <- get_included_subject_ids(file)

  df %>%
    filter(dim.top_level__subject_id %in% good_ids)
}
