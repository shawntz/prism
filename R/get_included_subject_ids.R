get_included_subject_ids = function(file) {
  read_csv(file) %>% 
    filter(exclude == "no") %>% 
    pull(subject_id)
}
