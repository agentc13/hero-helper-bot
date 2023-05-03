
TCL:
Import waitlist into participants (start command?) - TO
Create start command for league season - TO
Create end command for league season - TO
Division announcement command - TO
Weekly match announcement command (new and outstanding matches) - TO
Promote/demote command (auto assigns division roles?) - TO
Manual move player command? - TO
Manual player edit command - TO
Print database command - TO
Check in command - participants
Division standings command (also shows current/outstanding matches) - participants
Current/outstanding match command - participants
Report match score command - participants/TO

Other stuff:
Add role checks to commands once I get them working.
Add leveling system. (posts = xp, level up, leaderboard)
Add meme commands. (ala carl-bot)
Alt-art commands. (ala carl-bot)
Card lookup commands. (host image on server instead of web-scraping? Have cards for each class and add stuff from beta).
Command to add cards to lookup database.
On-Demand tournament (16 player single elim). Could use gambits for each event/match (make toggle for this?).
TO Helper (allow organizers to set up league/tournament through discord with various formats).
Database setup commands part of TO helper.
Allow admins/mods to add simple commands to add to memes/alt art card commands. (ala carl-bot)
Twitch/Youtube/etc announcements?











Start Command:
After divisions are set.
This will auto-assign roles to participants based on division setup.
Will populate the db with division (group_id), tournament_id, and seed fields.
Make announcement in each division channel of the player list and seeds.

End Command:
Will end the season when all games are finished.
Post the final standings in each division channel.
Copy the current (just ended) season's stats to JSON or similar in order to be able to reference for next season setup.
Makes a league announcement of players being promoted.

Promote/Demote Command:
Automatically promotes top 2 players in division based on tie-breakers. (this will have to reference the JSON backup).
Checks last season db and removes players that have not checked in to come back.
Integrates waitlist into new season db. (starting at lowest division)
Fills in rest of division slots starting at the top divisions based on last seasons stats. (when people drop).

Move Player command:
Moves player to a specified division.

Manual Player Edit command:
Allows TO to edit database fields for player in case it is necessary.

Show Database command:
Prints database data to TO discord channel so that TOs can see the data without using other software.

Division Announcement Command:
This will make an announcement in the league channel as well as all the division channels @'ing the appropriate roles.
Used in TO channel to just pump out league announcements

Weekly Matchup command:
Posts the weeks matchups in each division channel.
Posts all the outstanding matches @'ing the players.
Possibly runs on schedule instead of a / command.

Check In command:
Flags existing players as coming back for next season.

Division Standings command:
Posts the current division standings.
Shows current and outstanding matches?

Current/Outstanding Match command:
PMs player with current and outstanding matches.

Report match results command:
Allows players/TOs to report match results.