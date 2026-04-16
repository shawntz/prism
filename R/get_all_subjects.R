get_all_subjects = function(file) {
  read_csv(file) %>% 
    pull(subject_id)
}
