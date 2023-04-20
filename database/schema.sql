CREATE TABLE IF NOT EXISTS `waitlist` (
  `user_id` varchar(20) NOT NULL,
  `hr_ign` varchar(20) NOT NULL ,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `participants` (
    `participant_id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `tournament_id` int(9) NOT NULL,
    `user_id` varchar(20) NOT NULL,
    `hr_ign` varchar(20) NOT NULL,
    `checked_in` varchar(5) NOT NULL,
    `waiting_list` varchar(5) NOT NULL,
    `active` varchar(5) NOT NULL,
    `seed` int(5),
    `group_id` int(5),
    `wins` int(5),
    `losses` int(5)
);

CREATE TABLE IF NOT EXISTS `matches` (
    `match_id` varchar(5) NOT NULL,
    `tournament_id` int(9) NOT NULL,
    `state` varchar(10) NOT NULL ,
    `p1_id` varchar(20) NOT NULL ,
    `p2_id` varchar(20) NOT NULL,
    `winner` varchar(20) NOT NULL,
    `loser` varchar(20) NOT NULL,
    `round` int(5),
    `group_id` int(5),
    `p1_wins` int(5),
    `p1_losses` int(5)
)