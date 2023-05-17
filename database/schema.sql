CREATE TABLE IF NOT EXISTS `waitlist` (
  `user_id` varchar(20) NOT NULL,
  `hr_ign` varchar(20) NOT NULL ,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CREATE TABLE IF NOT EXISTS `participants` (
--     `user_id` varchar(20) NOT NULL,
--     `hr_ign` varchar(20) NOT NULL,
--     `group_id` int(5),
--     `wins` int(5),
--     `losses` int(5),
--     `opps_defeated` varchar(255)
-- );
