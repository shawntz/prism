get_all_subject_ids = function(file) {
  read_csv(file) %>% 
    pull(subject_id)
}
