get_good_subjects = function(file) {
  read_csv(file) %>% 
    filter(exclude == "no") %>% 
    pull(subject_id)
}
