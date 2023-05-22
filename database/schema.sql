CREATE TABLE IF NOT EXISTS `waitlist` (
  `user_id` varchar(20) NOT NULL,
  `hr_ign` varchar(20) NOT NULL ,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `tcl_participants` (
    `user_id` varchar(20) NOT NULL,
    `hr_ign` varchar(20) NOT NULL
);
