/* Remove the comments.status column, in favour of 'reviewed' and 'publishible' columns. */
ALTER TABLE `comments`
	ADD COLUMN `reviewed` TINYINT(1) UNSIGNED NOT NULL DEFAULT 0 AFTER `status`,
	ADD COLUMN `publishable` TINYINT(1) UNSIGNED NOT NULL DEFAULT 0 AFTER `reviewed`;
UPDATE comments SET reviewed = 0, publishable = 0 WHERE status LIKE '%%unreviewed%%';
UPDATE comments SET reviewed = 1, publishable = 1 WHERE status LIKE '%%publish%%';
UPDATE comments SET reviewed = 1, publishable = 0 WHERE status LIKE '%%trash%%';
ALTER TABLE comments DROP COLUMN `status`;

/* ------------------------------------------------------- */

/* Rearrange the media file columns */
/* part 1 of 2 */
ALTER TABLE `media_files`
	DROP COLUMN `width`,
	DROP COLUMN `height`,
	DROP COLUMN `bitrate`,
	DROP COLUMN `position`,
	DROP COLUMN `enable_player`,
	DROP COLUMN `enable_feed`,
	DROP COLUMN `is_original`,
	CHANGE COLUMN `type` `container` VARCHAR(10) CHARACTER SET ascii COLLATE ascii_general_ci NOT NULL;

/* ------------------------------------------------------- */

/* Add all of our new settings */
INSERT INTO `settings` VALUES
	(NULL, 'popularity_decay_exponent', '4'),
	(NULL, 'popularity_decay_lifetime', '36'),
	(NULL, 'rich_text_editor', 'tinymce'),
	(NULL, 'google_analytics_uacct', ''),
	(NULL, 'flash_player', 'flowplayer'),
	(NULL, 'html5_player', 'html5'),
	(NULL, 'player_type', 'best'),
	(NULL, 'featured_category', '1'),
	(NULL, 'max_upload_size', '314572800'),
	(NULL, 'ftp_storage', 'false'),
	(NULL, 'ftp_server', 'ftp.someserver.com'),
	(NULL, 'ftp_user', 'username'),
	(NULL, 'ftp_password', 'password'),
	(NULL, 'ftp_upload_directory', 'media'),
	(NULL, 'ftp_download_url', 'http://www.someserver.com/web/accessible/media/'),
	(NULL, 'ftp_upload_integrity_retries', '10'),
	(NULL, 'akismet_key',''),
	(NULL, 'akismet_url',''),
	(NULL, 'req_comment_approval', 'false');