verify_ids <- function(subject_ids, ids_to_exclude) {
  if (!all(ids_to_exclude %in% subject_ids)) {
    warning("ID mismatch!")
  } else {
    return(TRUE)
  }
}
