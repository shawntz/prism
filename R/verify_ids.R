verify_ids <- function(subject_ids, ids_to_exclude) {
  if (!all(ids_to_exclude %in% subject_ids)) {
    missing_ids <- setdiff(ids_to_exclude, subject_ids)
    warning(
      paste(
        "ID mismatch! Missing IDs:",
        paste(missing_ids, collapse = ", ")
      )
    )
    return(FALSE)
  } else {
    return(TRUE)
  }
}
