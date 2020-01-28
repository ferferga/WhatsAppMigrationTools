import os
import sqlite3
import progressbar
import sys
from getpass import getpass
import re
import imghdr

#If you moved your recent database versions using utilities like WinWazzapMigrator and so on without moving media, you should not change this.
#If you moved your media all along, you should set this to False
nomedia = True


def path_error():
    print("\n\nThe path was incorrect. Please, try again\n")
    return

def connect_database(display_text):
    while True:
        try:
            path = input(display_text)
            db_conn = sqlite3.connect(path)
            break
        except KeyboardInterrupt:
            raise KeyboardInterrupt
            break
        except:
            path_error()
    return db_conn

def optimize_database():
    try:
        db_temp = connect_database("Type the path of the ORIGINAL msgstore.db file: ")
        cursor = db_temp.cursor()
        print("\nStarting database optimization...")
        cursor.execute("PRAGMA integrity_check;")
        if cursor.fetchone()[0] == "ok":
            print("Database is healthy")
        else:
            print("Database is unhealthy. You must manually check the errors using 'PRAGMA integrity_check' in a database viewer like 'SQLite Browser'")
        cursor.execute("PRAGMA foreign_key_check;")
        try:
            if cursor.fetchone()[0] is not None:
                print("Relationship with tables are wrong. You must manually check the errors using 'PRAGMA foreign_key_check' in a database viewer like 'SQLite Browser'")
        except:
            pass
        cursor.execute("PRAGMA optimize;")
        cursor.execute("VACUUM")
        print("The database has been vacuumed and optimized!")
        db_temp.commit()
        db_temp.close()
    except KeyboardInterrupt:
        pass

try:
    print("Before starting, is suggested that you optimize the ORIGINAL (from your Android installation) msgstore.db database to accelerate writes.\
        \nPress Control-C if you want to skip and want to start moving calls right away\n")
    optimize_database()
except KeyboardInterrupt:
    pass

## Here, we move calls from WP to the new database in Android

try:
    print("\n\nWe start by moving calls. Press Control-C if you want to skip to fixing mentions\n")
    db_original = connect_database("Type the path of the calls.db (Windows Phone DB) file: ")
    db_msgstore = connect_database("Type the path of the ORIGINAL msgstore.db (Android DB) file: ")        
    llamadas = db_original.cursor()
    msgstore = db_msgstore.cursor()
    print("Processing data into the temporary database...")
    llamadas.execute("SELECT COUNT(*) FROM CallLog")
    callcount = llamadas.fetchone()[0]
    with progressbar.ProgressBar(max_value=callcount) as bar:
        loopCount = 0
        try:
            os.remove("tmp.db")
        except:
            pass
        tmp_db = sqlite3.connect("tmp.db")        
        tmp_cursor = tmp_db.cursor()
        tmp_cursor.execute("CREATE TABLE call_log (_id INTEGER PRIMARY KEY AUTOINCREMENT, jid_row_id INTEGER, from_me INTEGER, call_id TEXT, transaction_id INTEGER, timestamp INTEGER, video_call INTEGER, duration INTEGER, call_result INTEGER, bytes_transferred INTEGER)")
        tmp_cursor.execute("CREATE TABLE call_log_participant_v2 (_id INTEGER PRIMARY KEY AUTOINCREMENT, call_log_row_id INTEGER, jid_row_id INTEGER, call_result INTEGER)")
        tmp_cursor.execute("CREATE TABLE missed_call_log_participant (_id INTEGER PRIMARY KEY AUTOINCREMENT, call_logs_row_id INTEGER, jid TEXT, call_result INTEGER)")
        tmp_db.commit()
        llamadas.execute("SELECT * FROM CallLog")
        for row in llamadas:
            jid = row[1]
            call_id = "call:" + row[2]
            from_me = row[3]
            if row[5] is not None:
                duration = row[6] - row[4]
            else:
                duration = 0
            timestamp = str(row[4]) + "000"
            timestamp = int(timestamp)
            video_call = row[10]
            if video_call is None:
                video_call = 0
            result = row[7]
            bytes_transferred = row[8] + row[9]
            msgstore.execute("SELECT _id FROM jid WHERE raw_string = '" + jid + "'")
            jid_id = msgstore.fetchone()[0]
            reg = (row[0], jid_id, from_me, call_id, -1, timestamp, video_call, duration, result, bytes_transferred)
            tmp_cursor.execute("INSERT INTO call_log VALUES(?,?,?,?,?,?,?,?,?,?)", reg)
            loopCount = loopCount + 1
            bar.update(loopCount)
        tmp_db.commit()
    print("\n\nRemoving temporal database and moving changes to the original database...\n")
    msgstore.execute("SELECT * FROM call_log")
    for row in msgstore:
        reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
        tmp_cursor.execute("INSERT INTO call_log VALUES(?,?,?,?,?,?,?,?,?,?)", reg)
    tmp_db.commit()
    tmp_cursor.execute("CREATE TABLE call_log_temp (_id INTEGER PRIMARY KEY AUTOINCREMENT, jid_row_id INTEGER, from_me INTEGER, call_id TEXT, transaction_id INTEGER, timestamp INTEGER, video_call INTEGER, duration INTEGER, call_result INTEGER, bytes_transferred INTEGER)")
    tmp_cursor.execute("INSERT INTO call_log_temp SELECT * FROM call_log GROUP BY call_id")
    tmp_cursor.execute("DROP TABLE call_log")
    tmp_cursor.execute("ALTER TABLE call_log_temp RENAME TO call_log")
    tmp_db.commit()
    tmp_cursor2 = tmp_db.cursor()
    msgstore2 = db_msgstore.cursor()
    msgstore.execute("SELECT cl.*, c.call_id FROM call_log_participant_v2 cl JOIN call_log c ON c._id=cl.call_log_row_id")
    for row in msgstore:
        tmp_cursor.execute("SELECT _id FROM call_log WHERE call_id = '" + str(row[4]) + "'")
        new_id = tmp_cursor.fetchone()[0]
        reg = (None, new_id, row[2], row[3])
        tmp_cursor2.execute("INSERT INTO call_log_participant_v2 VALUES(?,?,?,?)", reg)    
    msgstore.execute("SELECT mc._id, c.call_id, mc.jid, mc.call_result FROM call_log c JOIN missed_call_log_participant mc ON c._id=mc.call_logs_row_id;")
    for row in msgstore:
        tmp_cursor.execute("SELECT _id FROM call_log WHERE call_id = ?", (row[1]))
        call_id = tmp_cursor.fetchone()[0]
        reg = (None, call_id, row[2], row[3])
        tmp_cursor2.execute("INSERT INTO missed_call_log_participant VALUES(?,?,?,?)")
    tmp_db.commit()
    msgstore.execute("DELETE FROM call_log")
    msgstore.execute("DELETE FROM call_log_participant_v2")
    msgstore.execute("DROP INDEX IF EXISTS call_log_key_index")
    msgstore.execute("DROP INDEX IF EXISTS call_log_participant_key_index")
    msgstore.execute("CREATE UNIQUE INDEX call_log_key_index on call_log (jid_row_id, from_me, call_id, transaction_id)")
    msgstore.execute("CREATE UNIQUE INDEX call_log_participant_key_index on call_log_participant_v2 (call_log_row_id, jid_row_id)")
    msgstore.execute("DELETE FROM sqlite_sequence WHERE name = 'call_log' OR name = 'call_log_participant_v2' OR name = 'missed_call_log_participant'")
    db_msgstore.commit()
    tmp_cursor.execute("SELECT * FROM call_log ORDER BY timestamp ASC")
    for row in tmp_cursor:
        reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
        try:
            msgstore.execute("INSERT INTO call_log VALUES(?,?,?,?,?,?,?,?,?,?)", reg)
        except:
            continue
    tmp_cursor.execute("SELECT * FROM call_log_participant_v2")
    for row in tmp_cursor:
        reg = (None, row[1], row[2], row[3])
        try:
            msgstore.execute("INSERT INTO call_log_participant_v2 VALUES(?,?,?,?)", reg)
        except:
            continue
    tmp_cursor.execute("SELECT * FROM missed_call_log_participant")
    for row in tmp_cursor:
        reg = (row[0], row[1], row[2], row[3])
        try:
            msgstore.execute("INSERT INTO missed_call_log_participant VALUES(?,?,?,?)", reg)
        except:
            continue
    db_msgstore.commit()
    tmp_db.commit()
    tmp_db.close()
    os.remove("tmp.db")
    db_msgstore.commit()
    db_msgstore.close()
    db_original.close()
    print("\nCalls part is completed!")
except KeyboardInterrupt:
    pass

## Here, we fix mentions

try:
    print("\n\nWe start fixing mentions. Press Control-C if you want to skip to adding missing messages and media\n")
    db_msgstore = connect_database("Type the path of the ORIGINAL msgstore.db (Android DB) file: ")
    msgstore = db_msgstore.cursor()
    msgstore2 = db_msgstore.cursor()
    msgstore3 = db_msgstore.cursor()
    print("\n\nUpdating normal messages...\n")
    msgstore.execute("SELECT COUNT(*) FROM messages WHERE data LIKE '%@%' AND mentioned_jids IS NULL")
    msgcount = msgstore.fetchone()[0]
    with progressbar.ProgressBar(max_value=msgcount) as bar:
        loopCount = 0
        msgstore.execute("SELECT data, _id FROM messages WHERE data LIKE '%@%' AND mentioned_jids IS NULL")
        for row in msgstore:
            _id = row[1]
            appendComma = False
            composite_text = ""
            mention_array = re.findall("(@[0-9]+[^\s])", row[0])
            if len(mention_array) == 0:
                continue
            if len(mention_array) > 1:
                appendComma = True
            for mention in mention_array:
                mention = mention.replace("@", "")
                msgstore2.execute("SELECT COUNT(_id) FROM jid WHERE user = '" + mention + "'")
                row_count = msgstore2.fetchone()[0]
                if row_count != 0:
                    msgstore2.execute("SELECT raw_string FROM jid WHERE user = '" + mention + "'")
                    composite_text = composite_text + msgstore2.fetchone()[0]
                if appendComma:
                    composite_text = composite_text + ","
            if appendComma:
                composite_text = composite_text[:-1]
            msgstore3.execute("UPDATE messages SET mentioned_jids = '" + composite_text + "' WHERE _id = " + str(_id))
            loopCount = loopCount + 1
            bar.update(loopCount)
        db_msgstore.commit()
    print("\n\nFinished normal messages. Repeating procedure for 'messages_quotes' table...")
    msgstore.execute("SELECT COUNT(*) FROM messages_quotes WHERE data LIKE '%@%'")
    msgcount = msgstore.fetchone()[0]
    with progressbar.ProgressBar(max_value=msgcount) as bar:
        loopCount = 0
        msgstore.execute("SELECT data, _id FROM messages_quotes WHERE data LIKE '%@%' AND mentioned_jids IS NULL")
        for row in msgstore:
            _id = row[1]
            appendComma = False
            composite_text = ""
            mention_array = re.findall("(@[0-9]+[^\s])", row[0])
            if len(mention_array) == 0:
                continue
            if len(mention_array) > 1:
                appendComma = True
            for mention in mention_array:
                mention = mention.replace("@", "")
                msgstore2.execute("SELECT COUNT(_id) FROM jid WHERE user = '" + mention + "'")
                row_count = msgstore2.fetchone()[0]
                if row_count != 0:
                    msgstore2.execute("SELECT raw_string FROM jid WHERE user = '" + mention + "'")
                    composite_text = composite_text + msgstore2.fetchone()[0]
                if appendComma:
                    composite_text = composite_text + ","
            if appendComma:
                composite_text = composite_text[:-1]
            msgstore3.execute("UPDATE messages_quotes SET mentioned_jids = '" + composite_text + "' WHERE _id = " + str(_id))
            loopCount = loopCount + 1
            bar.update(loopCount)
        db_msgstore.commit()
    print("Fixing mentions part completed successfully")
except KeyboardInterrupt:
    pass

## Here we add missing media and missing messages

try:
    print("\n\nWe start adding missing media and messages. Press Control-C if you want to skip to fixing replies (NOT RECOMMENDED).\n")
    orig_msgstore = connect_database("Type the path of the ORIGINAL msgstore.db (Android DB) file: ")
    alt_msgstore = connect_database("Type the path of msgstore.db (The file produced by my other script) file: ")
    messages_db = connect_database("Type the path of messages.db (The original Windows Phone database): ")
    print()
    orig = orig_msgstore.cursor()
    orig.execute("PRAGMA synchronous")
    pragma_level = orig.fetchone()[0]
    orig.execute("PRAGMA synchronous = OFF")
    orig.execute("PRAGMA cache_size = 999999")
    orig.execute("PRAGMA journal_mode")
    journal_mode = orig.fetchone()[0]
    orig.execute("PRAGMA journal_mode = MEMORY;")
    orig.execute("PRAGMA temp_store;")
    temp_store_mode = orig.fetchone()[0]
    orig.execute("PRAGMA temp_store = MEMORY;")    
    orig.execute("BEGIN TRANSACTION")
    alt = alt_msgstore.cursor()
    alt2 = alt_msgstore.cursor()
    media_keys_original = {}
    messages_cur = messages_db.cursor()
    messages_cur.execute("SELECT KeyId, MediaKey FROM messages")
    for row in messages_cur:
        media_keys_original[str(row[0])] = row[1]
    messages_db.close()
    del messages_db
    del messages_cur
    quoted_keys = []
    alt_keys = []
    alt_media_type = []
    alt_quotes_media_type = []
    jid_relationship = {}
    chat_relationship = {}
    orig.execute("SELECT _id, raw_string FROM jid")
    for row in orig:
        jid_relationship[str(row[1])] = row[0]
    orig.execute("SELECT _id, jid_row_id FROM chat")
    for row in orig:
        chat_relationship[int(row[1])] = row[0]
    # Some documents without thumbnails and re-key notifications gave problems, so we skip them (media types 7 and 8) and stickers (19,20)
    alt.execute("SELECT key_id, media_wa_type FROM messages WHERE key_id NOT IN (SELECT key_id FROM messages WHERE media_wa_type == 7 OR media_wa_type == 8 OR media_wa_type == 19\
        OR media_wa_type == 20) GROUP BY key_id")
    for msg in alt:
        alt_keys.append(msg[0])
        alt_media_type.append(msg[1])
    msgcount = len(alt_keys)
    alt.execute("SELECT key_id, media_wa_type FROM messages_quotes WHERE key_id NOT IN (SELECT key_id FROM messages_quotes WHERE media_wa_type == 7 OR media_wa_type == 8\
        OR media_wa_type == 19 OR media_wa_type == 20) GROUP BY key_id")
    for row in alt:
        quoted_keys.append(row[0])
        alt_quotes_media_type.append(row[1])
    msgcount = msgcount + len(quoted_keys)
    alt.execute ("SELECT COUNT(key_id) FROM message_thumbnails")
    msgcount = msgcount + alt.fetchone()[0]
    with progressbar.ProgressBar(max_value=(msgcount+3)) as bar:
        bar.start()
        loopCount = 0
        keys_msgstore = []
        media_types_msgstore = []
        media_types_quoted_msgstore = []
        keys_quoted_msgstore = []
        orig.execute("SELECT key_id, media_wa_type FROM messages GROUP BY key_id")
        for row in orig:
            keys_msgstore.append(row[0])
            media_types_msgstore.append(row[1])
        loopCount = loopCount + 1
        bar.update(loopCount)
        orig.execute("SELECT key_id, media_wa_type FROM messages_quotes GROUP BY key_id")
        for row in orig:
            keys_quoted_msgstore.append(row[0])
            media_types_quoted_msgstore.append(row[1])
        loopCount = loopCount + 1
        bar.update(loopCount)
        msg_quotes_rows = {}
        msg_rows = {}        
        alt.execute("SELECT _id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count FROM messages_quotes WHERE key_id NOT IN \
                (SELECT key_id FROM messages_quotes WHERE media_wa_type == 7 OR media_wa_type == 8 OR media_wa_type == 19 OR media_wa_type == 20)")
        for row in alt:
            msg_quotes_rows[str(row[3])] = row
        alt.execute("SELECT _id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count FROM messages WHERE key_id NOT IN \
                (SELECT key_id FROM messages WHERE media_wa_type == 7 OR media_wa_type == 8 OR media_wa_type == 19 OR media_wa_type == 20)")
        for row in alt:
            msg_rows[str(row[3])] = row
        for index, key in enumerate(quoted_keys, 0):
            if key not in keys_quoted_msgstore:
                row = msg_quotes_rows[str(key)]
                # Here we skip an strange media type used by WhatsApp in some messages of all formats. So no way to handle it in a 100% confident way. 
                # All messages with that media type ended up crashing the app during my testing
                if int(row[10]) >= 1000:
                    continue
                if row[31] != 0:
                    reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14],
                        row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29],
                        row[30], -5, row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39])
                else:
                    reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14],
                        row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29],
                        row[30], 0, row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39])
                orig.execute("INSERT INTO messages_quotes (_id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                        timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                        latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                        raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                        multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count) \
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
            loopCount = loopCount+1
            bar.update(loopCount)
        for index, key in enumerate(alt_keys, 0):
            if key not in keys_msgstore:
                row = msg_rows[str(key)]
                # Same as above
                if int(row[10]) >= 1000:
                    continue
                if row[31] != 0:
                    reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14],
                        row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29],
                        row[30], -5, row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39])
                else:
                    reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14],
                        row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29],
                        row[30], 0, row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39])
                orig.execute("INSERT INTO messages (_id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                        timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                        latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                        raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                        multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count) \
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
                try:
                    chat_id = chat_relationship[jid_relationship[row[1]]]
                    mediakey = media_keys_original[row[3]]
                    reg2 = (orig.lastrowid, chat_id, 0, None, None, 1, 1, None, row[11], 0, 0, 0, 0, 0, mediakey, row[7], 1000, 1000, 0, 0, 1.0, \
                        None, None, None, row[8], row[9], row[11], row[12], row[13], row[14], 0, None, None, None, 0)
                    orig.execute("INSERT INTO message_media(message_row_id, chat_row_id, autotransfer_retry_enabled, multicast_id, media_job_uuid, transferred, \
                        transcoded, file_path, file_size, suspicious_content, trim_from, trim_to, face_x, face_y, media_key, media_key_timestamp, width, height, \
                        has_streaming_sidecar, gif_attribution, thumbnail_height_width_ratio, direct_path, first_scan_sidecar, first_scan_length, \
                        message_url, mime_type, file_length, media_name, file_hash, media_duration, page_count, enc_file_hash, partial_media_hash, \
                        partial_media_enc_hash, is_animated_sticker) \
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg2)
                except:
                    pass
            loopCount = loopCount+1
            bar.update(loopCount)
        orig_msgstore.commit()
        msg_rows.clear()
        msg_quotes_rows.clear()
        del msg_rows
        del msg_quotes_rows
        thumbnails_keys = []
        orig.execute("SELECT key_id FROM message_thumbnails")
        for row in orig:
            thumbnails_keys.append(row[0])
        alt.execute("SELECT * FROM message_thumbnails")
        for row in alt:
            if row[4] not in thumbnails_keys:
                reg = (row[0], row[1], row[2], row[3], row[4])
                orig.execute("INSERT INTO message_thumbnails VALUES(?,?,?,?,?)", reg)
            loopCount = loopCount+1
            bar.update(loopCount)
    print()
    media_keys_original.clear()
    thumbnails_keys.clear()
    keys_msgstore.clear()
    media_types_msgstore.clear()
    media_types_quoted_msgstore.clear()
    keys_quoted_msgstore.clear()
    quoted_keys.clear()
    alt_keys.clear()
    alt_media_type.clear()
    alt_quotes_media_type.clear()
    orig.execute("COMMIT")
    orig_msgstore.commit()
    orig.execute("PRAGMA synchronous = " + str(pragma_level))
    orig.execute("PRAGMA journal_mode = " + str(journal_mode))
    orig.execute("PRAGMA temp_store = " + str(temp_store_mode))
    orig_msgstore.commit()
    orig_msgstore.close()
    alt_msgstore.close()
    print("Added missing messages and media from the alternative database.\n\n¡¡¡¡¡YOU ARE ADVISED TO FIX REPLIES AND SORT THE DATABASE AFTER THIS!!!!!")
except KeyboardInterrupt:
    pass

## Here we fix replies

try:
    print("\n\nWe start fixing replies. Press Control-C if you want to skip to cleaning database.\nMAKE SURE THAT YOU HAVE FINISHED ADDING MISSING MESSAGES BEFORE, \
OTHERWISE SOME DATA MIGHT BE MISSING\n")
    db_temp = connect_database("Type the path of the temp.db (generated by my other script) file: ")
    db_msgstore = connect_database("Type the path of the ORIGINAL msgstore.db (Android DB) file: ")
    tmp = db_temp.cursor()
    msgstore = db_msgstore.cursor()
    msg_quotes_dict = {}
    msg_keys = []
    msg_quote_keys = []
    msgstore.execute("SELECT _id, key_id FROM messages_quotes")
    for row in msgstore:
        msg_quotes_dict[str(row[1])] = row[0]        
    msgstore.execute("SELECT key_id FROM messages")
    for row in msgstore:
        msg_keys.append(row[0])
    msgstore.execute("SELECT key_id FROM messages_quotes")
    for row in msgstore:
        msg_quote_keys.append(row[0])
    msgstore.execute("PRAGMA synchronous")
    pragma_level = msgstore.fetchone()[0]
    msgstore.execute("PRAGMA synchronous = OFF")
    msgstore.execute("PRAGMA cache_size = 999999")
    msgstore.execute("PRAGMA journal_mode")
    journal_mode = msgstore.fetchone()[0]
    msgstore.execute("PRAGMA journal_mode = MEMORY;")
    msgstore.execute("PRAGMA temp_store;")
    temp_store_mode = msgstore.fetchone()[0]
    msgstore.execute("PRAGMA temp_store = MEMORY;")
    msgstore.execute("BEGIN TRANSACTION")
    tmp.execute("SELECT COUNT(quote_key_id) FROM definitive_replies")
    msgcount = tmp.fetchone()[0]+1
    print()
    with progressbar.ProgressBar(max_value=msgcount) as bar:
        loopCount = 0
        msgstore.execute("UPDATE messages SET quoted_row_id = 0 WHERE quoted_row_id IS NULL")
        msgstore.execute("UPDATE messages_quotes SET quoted_row_id = 0 WHERE quoted_row_id IS NULL")
        db_msgstore.commit()        
        loopCount = loopCount + 1
        bar.update(loopCount)
        tmp.execute("SELECT quote_key_id, quoted_key_id FROM definitive_replies")
        for row in tmp:
            try:
                reg = (msg_quotes_dict[str(row[1])], row[0])
            except:
                loopCount = loopCount + 1
                bar.update(loopCount)
                continue
            if row[0] in msg_keys:
                msgstore.execute("UPDATE messages SET quoted_row_id = ? WHERE key_id = ?;", reg)
            if row[0] in msg_quote_keys:
                msgstore.execute("UPDATE messages_quotes SET quoted_row_id = ? WHERE key_id = ?;", reg)
            loopCount = loopCount + 1
            bar.update(loopCount)
        db_msgstore.commit()
        msg_quotes_dict.clear()
        msg_keys.clear()
        msg_quote_keys.clear()
        del msg_quotes_dict
        del msg_keys
        del msg_quote_keys
        msgstore.execute("PRAGMA synchronous = " + str(pragma_level))
        msgstore.execute("PRAGMA journal_mode = " + str(journal_mode))
        msgstore.execute("PRAGMA temp_store = " + str(temp_store_mode))
        db_msgstore.commit()
        db_msgstore.close()
        db_temp.close()
    print("Fixing replies part completed successfully")
except KeyboardInterrupt:
    pass

# Clean up unnecesary data:

# try:
#     print("\n\nUNSAFE! We start cleaning up seemingly unnecessary data according to ferferga's tests. Press Control-C if you want to skip to adding missing media\n")
#     db_msgstore = connect_database("Type the path of the ORIGINAL msgstore.db (Android DB) file: ")
#     msgstore = db_msgstore.cursor()
#     msgstore.execute("DELETE FROM message_fts_content")
#     msgstore.execute("DELETE FROM message_fts")
#     msgstore.execute("DELETE FROM message_fts_docsize")
#     msgstore.execute("DELETE FROM message_fts_segdir")
#     msgstore.execute("DELETE FROM message_fts_segments")
#     msgstore.execute("DELETE FROM message_fts_stat")
#     msgstore.execute("DELETE FROM messages_fts")
#     msgstore.execute("DELETE FROM messages_fts_content")
#     msgstore.execute("DELETE FROM messages_fts_segdir")
#     msgstore.execute("DELETE FROM messages_fts_segments")
#     msgstore.execute("DELETE FROM labeled_messages_fts")
#     msgstore.execute("DELETE FROM labeled_messages_fts_content")
#     msgstore.execute("DELETE FROM labeled_messages_fts_segdir")
#     msgstore.execute("DELETE FROM labeled_messages_fts_segments")
#     msgstore.execute("DELETE FROM props WHERE key = 'fts_index_start'")
#     msgstore.execute("DELETE FROM message_streaming_sidecar WHERE timestamp > (SELECT strftime('%s', date('now', '-2 month')));")
#     print("\n\nDeleted unnecessary data!")
#     confirm = input("Do you want to add a trigger to the database, so everytime WhatsApp does a change in the unnecessary tables a cleanup is automatically done?\n\
#         THIS MIGHT BE UNSAFE IN THE LONG TERM IF WHATSAPP DOES CHANGES THAT REQUIRES YOU TO REMOVE THIS TRIGGER! ONLY SAY YES IF YOU KNOW HOW TO DELETE THE TRIGGER AFTERWARDS\
#         IN CASE SOMETHING UNEXPECTED HAPPEN IN THE FUTURE\nShall I do it (Y|N)?: ")
#     while True:
#         if confirm.upper() == "Y" or confirm.upper() == "N":
#             break
#         else:
#             print("\nIncorrect option. Repeat again\n")
#             confirm = input("Do you want to add a trigger to the database, so everytime WhatsApp does a change in the unnecessary tables a cleanup is automatically done?\n\
#     THIS MIGHT BE UNSAFE IN THE LONG TERM IF WHATSAPP DOES CHANGES THAT REQUIRES YOU TO REMOVE THIS TRIGGER! ONLY SAY YES IF YOU KNOW HOW TO DELETE THE TRIGGER AFTERWARDS\
#     IN CASE SOMETHING UNEXPECTED HAPPEN IN THE FUTURE\nShall I do it (Y|N)?: ")
#     if confirm.upper() == "Y":
#         msgstore.execute("CREATE TRIGGER ferferga_cleanup_trigger AFTER INSERT ON messages")
#     db_msgstore.commit()
#     db_msgstore.close()
# except KeyboardInterrupt:
#     pass

#Sort database
try:
    print("\n\nWe start sorting IDs in the database. Press Control-C if you want to skip to database optimization.\nTHIS IS HIGHLY RECOMMENDED AFTER ADDING MISSING MESSAGES.\n")
    db_msgstore = connect_database("Type the path of the ORIGINAL msgstore.db (Android DB) file: ")
    print("\nInitializing... This might take a while...")
    try:
        os.remove("wa_sorting_data.db")
    except:
        pass
    db_temp = sqlite3.connect(":memory:")
    tmp = db_temp.cursor()
    msgstore = db_msgstore.cursor()
    msgstore2 = db_msgstore.cursor()
    tmp.execute("PRAGMA synchronous = OFF")
    tmp.execute("PRAGMA cache_size = 999999")
    tmp.execute("PRAGMA journal_mode = MEMORY;")
    tmp.execute("PRAGMA temp_store = MEMORY;")
    tmp.execute("CREATE TABLE messages (_id INTEGER PRIMARY KEY AUTOINCREMENT,key_remote_jid TEXT NOT NULL,key_from_me INTEGER,key_id TEXT NOT NULL,status INTEGER,\
        needs_push INTEGER,data TEXT,timestamp INTEGER,media_url TEXT,media_mime_type TEXT,media_wa_type TEXT,media_size INTEGER,media_name TEXT,media_hash TEXT,\
        media_duration INTEGER,origin INTEGER,latitude REAL,longitude REAL,thumb_image TEXT,remote_resource TEXT,received_timestamp INTEGER,send_timestamp INTEGER,\
        receipt_server_timestamp INTEGER,receipt_device_timestamp INTEGER,raw_data BLOB,recipient_count INTEGER,media_caption TEXT,starred INTEGER,\
        read_device_timestamp INTEGER, played_device_timestamp INTEGER, participant_hash TEXT, quoted_row_id INTEGER, mentioned_jids TEXT, \
        multicast_id TEXT, edit_version INTEGER, media_enc_hash TEXT, payment_transaction_id TEXT, forwarded INTEGER, preview_type INTEGER, send_count INTEGER)")
    tmp.execute("CREATE TABLE messages_quotes (_id INTEGER PRIMARY KEY AUTOINCREMENT, key_remote_jid TEXT NOT NULL, key_from_me INTEGER, \
        key_id TEXT NOT NULL, status INTEGER, needs_push INTEGER, data TEXT, timestamp INTEGER, media_url TEXT, media_mime_type TEXT, \
        media_wa_type TEXT, media_size INTEGER, media_name TEXT, media_caption TEXT, media_hash TEXT, media_duration INTEGER, origin INTEGER, \
        latitude REAL, longitude REAL, thumb_image TEXT, remote_resource TEXT, received_timestamp INTEGER, send_timestamp INTEGER, \
        receipt_server_timestamp INTEGER, receipt_device_timestamp INTEGER, read_device_timestamp INTEGER, played_device_timestamp INTEGER, \
        raw_data BLOB, recipient_count INTEGER, participant_hash TEXT, starred INTEGER, quoted_row_id INTEGER, mentioned_jids TEXT, \
        multicast_id TEXT, edit_version INTEGER, media_enc_hash TEXT, payment_transaction_id TEXT, forwarded INTEGER, preview_type INTEGER, send_count INTEGER)")
    tmp.execute("CREATE TABLE message_thumbnails (thumbnail BLOB, timestamp DATETIME, key_remote_jid TEXT NOT NULL, key_from_me INTEGER, key_id TEXT NOT NULL)")
    tmp.execute("CREATE TABLE message_media (message_row_id INTEGER PRIMARY KEY, chat_row_id INTEGER, autotransfer_retry_enabled INTEGER, multicast_id TEXT,\
        media_job_uuid TEXT, transferred INTEGER, transcoded INTEGER, file_path TEXT, file_size INTEGER, suspicious_content INTEGER, trim_from INTEGER,\
        trim_to INTEGER, face_x INTEGER, face_y INTEGER, media_key BLOB, media_key_timestamp INTEGER, width INTEGER, height INTEGER,\
        has_streaming_sidecar INTEGER, gif_attribution INTEGER, thumbnail_height_width_ratio REAL, direct_path TEXT, first_scan_sidecar BLOB,\
        first_scan_length INTEGER, message_url TEXT, mime_type TEXT, file_length INTEGER, media_name TEXT, file_hash TEXT, media_duration INTEGER,\
        page_count INTEGER, enc_file_hash TEXT, partial_media_hash TEXT, partial_media_enc_hash TEXT, is_animated_sticker INTEGER)")
    tmp.execute("CREATE TABLE keys_relationship (key_id TEXT PRIMARY KEY, old_id_messages INTEGER, new_id_messages INTEGER, old_id_quotes INTEGER, new_id_quotes INTEGER)")
    tmp.execute("CREATE TABLE quotes (quoted_key_id TEXT NOT NULL, quote_key_id TEXT NOT NULL)")
    db_temp.commit()
    msgstore.execute("SELECT COUNT(_id) FROM messages")
    msgcount = msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(_id) FROM messages_quotes")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(key_id) FROM message_thumbnails")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(quoted_key_id) FROM \
        (SELECT DISTINCT * FROM (SELECT qed.key_id quoted_key_id, q.key_id quote_key_id FROM messages_quotes qed JOIN messages_quotes q ON qed._id=q.quoted_row_id UNION \
        SELECT qed.key_id quoted_key_id, q.key_id quote_key_id FROM messages q JOIN messages_quotes qed ON qed._id=q.quoted_row_id))")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(message_row_id) FROM message_media")
    msgcount = msgcount + msgstore.fetchone()[0] * 2
    print("\nNow backing up data into the temporary database...\n")
    # Sometimes, quotes from groups into private chats and deleted messages might be still in messages_quotes while not present in messages, that means that we need
    # to take care of them individually, in different loops, instead of doing them all at once in a single loop.
    with progressbar.ProgressBar(max_value=msgcount+1) as bar:
        loopcount = 0
        msgstore.execute("SELECT _id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                    timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                    latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                    raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                    multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count FROM messages GROUP BY key_id \
                    ORDER BY timestamp ASC")
        for index, row in enumerate(msgstore):
            reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14],
                row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29],
                row[30], row[31], row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39])
            tmp.execute("INSERT INTO messages (_id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                            timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                            latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                            raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                            multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count) \
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT _id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                    timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                    latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                    raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                    multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count FROM messages_quotes GROUP BY key_id\
                    ORDER BY timestamp ASC")
        for index, row in enumerate(msgstore):
            reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14],
                row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29],
                row[30], row[31], row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39])
            tmp.execute("INSERT INTO messages_quotes (_id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                            timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                            latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                            raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                            multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count) \
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
            loopcount = loopcount + 1
            bar.update(loopcount)
        quotes_keys = {}
        new_message_keys = {}
        new_quotes_keys = {}
        msgstore.execute("SELECT _id, key_id FROM messages_quotes")
        for row in msgstore:
            quotes_keys[str(row[1])] = int(row[0])            
        tmp.execute("SELECT _id, key_id FROM messages")
        for row in tmp:
            new_message_keys[str(row[1])] = int(row[0])
        tmp.execute("SELECT _id, key_id FROM messages_quotes")
        for row in tmp:
            new_quotes_keys[str(row[1])] = int(row[0])
        msgstore.execute("SELECT key_id, _id FROM messages")
        for row in msgstore:
            try:
                new_id = new_message_keys[row[0]]
            except:
                new_id = None
            try:
                new_quote_id = new_quotes_keys[row[0]]
                old_quote_id = quotes_keys[row[0]]
            except:
                new_quote_id = None
                old_quote_id = None
            reg2 = (row[0], row[1], new_id, old_quote_id, new_quote_id)
            try:
                tmp.execute("INSERT INTO keys_relationship VALUES(?,?,?,?,?)", reg2)
            except:
                pass
        msgstore.execute("SELECT key_id, _id FROM messages WHERE key_id NOT IN (SELECT key_id FROM messages)")
        for row in msgstore:
            try:
                new_quote_id = new_quotes_keys[row[0]]
                old_quote_id = quotes_keys[row[0]]
            except:
                new_quote_id = None
                old_quote_id = None
            reg2 = (row[0], None, None, old_quote_id, new_quote_id)
            try:
                tmp.execute("INSERT INTO keys_relationship VALUES(?,?,?,?,?)", reg2)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        quotes_keys.clear()
        new_message_keys.clear()
        new_quotes_keys.clear()
        del quotes_keys
        del new_message_keys
        del new_quotes_keys
        msgstore.execute("SELECT * FROM message_thumbnails GROUP BY key_id ORDER BY timestamp ASC")
        for row in msgstore:
            reg = (row[0], row[1], row[2], row[3], row[4])
            tmp.execute("INSERT INTO message_thumbnails VALUES(?,?,?,?,?)", reg)
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT * FROM message_media ORDER BY media_key_timestamp ASC")
        for row in msgstore:
            reg = (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17],\
                row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29], row[30], row[31], row[32], row[33], row[34])
            tmp.execute("INSERT INTO message_media VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT DISTINCT * FROM (SELECT qed.key_id quoted_key_id, q.key_id quote_key_id FROM messages_quotes qed JOIN messages_quotes q ON qed._id=q.quoted_row_id UNION\
        SELECT qed.key_id quoted_key_id, q.key_id quote_key_id FROM messages q JOIN messages_quotes qed ON qed._id=q.quoted_row_id)")
        for row in msgstore:
            reg = (row[0], row[1])
            tmp.execute("INSERT INTO quotes VALUES(?,?)", reg)
            loopcount = loopcount + 1
            bar.update(loopcount)
        tmp.execute("UPDATE messages SET starred = 0 WHERE starred IS NULL")
        tmp.execute("UPDATE messages_quotes SET starred = 0 WHERE starred IS NULL")
        db_temp.commit()

    print("\nBacked up data successfully. Deleting original data from msgstore.db and restoring...\n")
    msgcount = msgcount
    msgstore.execute("SELECT COUNT(*) FROM chat")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM chat_list")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM deleted_chat_job")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM labeled_messages")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_ephemeral")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_forwarded")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_future")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_group_invite")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_link")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_location")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_media_interactive_annotation")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_mentions")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_payment")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_payment_status_update")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_payment_transaction_reminder")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_product")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_quoted")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_quoted_group_invite")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_quoted_group_invite_legacy")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_quoted_location")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_quoted_media")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_quoted_mentions")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_quoted_product")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_quoted_text")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_quoted_vcard")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_revoked")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_send_count")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_streaming_sidecar")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_system")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_system_block_contact")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_system_chat_participant")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_system_device_change")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_system_ephemeral_setting_change")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_system_group")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_system_number_change")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_system_photo_change")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_system_value_change")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_template")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_template_button")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_template_quoted")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_text")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_thumbnail")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM message_vcard")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM messages_dehydrated_hsm")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM messages_hydrated_four_row_template")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM messages_links")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM messages_vcards")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM messages_vcards_jids")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM missed_call_logs")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM pay_transaction")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM quoted_message_product")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM receipt_device")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM receipt_user")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM status")
    msgcount = msgcount + msgstore.fetchone()[0]
    msgstore.execute("SELECT COUNT(*) FROM status_list")
    msgcount = msgcount + msgstore.fetchone()[0]
    with progressbar.ProgressBar(max_value=msgcount) as bar:
        loopcount = 0
        triggers_queries = []
        triggers_names = []
        fts_names = []
        fts_queries = []
        msgstore.execute("SELECT sql, name FROM sqlite_master WHERE type = 'trigger' AND sql IS NOT NULL")
        for row in msgstore:
            triggers_queries.append(row[0])
            triggers_names.append(row[1])
        for trigger in triggers_names:
            msgstore.execute("DROP TRIGGER " + trigger)
        msgstore.execute("SELECT sql FROM sqlite_master WHERE sql LIKE '%VIRTUAL TABLE%' AND sql IS NOT NULL")
        for row in msgstore:
            fts_queries.append(row[0])
        fts_object_name = []
        fts_object_type = []
        msgstore.execute("SELECT type, name FROM sqlite_master WHERE name LIKE '%fts%'")
        for row in msgstore:
            fts_object_name.append(row[1])
            fts_object_type.append(row[0])
        for index, obj in enumerate(fts_object_type):
            msgstore2.execute("DROP " + obj + " IF EXISTS " + fts_object_name[index])
        fts_object_name.clear()
        fts_object_type.clear()
        del fts_object_name
        del fts_object_type
        db_msgstore.commit()
        triggers_names.clear()
        del triggers_names
        msgstore.execute("PRAGMA synchronous")
        pragma_level = msgstore.fetchone()[0]
        msgstore.execute("PRAGMA synchronous = OFF")
        msgstore.execute("PRAGMA cache_size = 999999")
        msgstore.execute("PRAGMA journal_mode")
        journal_mode = msgstore.fetchone()[0]
        msgstore.execute("PRAGMA journal_mode = MEMORY;")
        msgstore.execute("PRAGMA temp_store;")
        temp_store_mode = msgstore.fetchone()[0]
        msgstore.execute("PRAGMA temp_store = MEMORY;")
        msgstore.execute("DELETE FROM messages")
        msgstore.execute("DELETE FROM messages_quotes")
        msgstore.execute("DELETE FROM message_thumbnails")
        msgstore.execute("DELETE FROM message_media")
        db_msgstore.commit()     
        msgstore.execute("DELETE FROM sqlite_sequence WHERE name = 'messages' OR name = 'messages_quotes'")
        msgstore.execute("DELETE FROM props WHERE key = 'fts_index_start'")
        msgstore.execute("UPDATE props SET value = 0 WHERE key = 'fts_ready'")
        msg_quotes = {}
        tmp.execute("SELECT kr.new_id_quotes new_id, q.quote_key_id FROM quotes q JOIN keys_relationship kr ON kr.key_id=q.quoted_key_id")
        for row in tmp:
            msg_quotes[str(row[1])] = row[0]
        tmp.execute("SELECT _id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
            timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
            latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
            raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
            multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count FROM messages_quotes")
        for row in tmp:
            try:
                quoted_row_id = msg_quotes[str(row[3])]
            except:
                quoted_row_id = 0
            reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14],
                row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29],
                row[30], quoted_row_id, row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39])
            msgstore.execute("INSERT INTO messages_quotes (_id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count) \
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
            loopcount = loopcount + 1
            bar.update(loopcount)
        tmp.execute("SELECT _id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
            timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
            latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
            raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
            multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count FROM messages")
        for row in tmp:
            try:
                quoted_row_id = msg_quotes[str(row[3])]
            except:
                quoted_row_id = 0
            reg = (None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14],
                    row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29],
                    row[30], quoted_row_id, row[32], row[33], row[34], row[35], row[36], row[37], row[38], row[39])
            msgstore.execute("INSERT INTO messages (_id,key_remote_jid,key_from_me,key_id,status,needs_push,data,\
                timestamp,media_url,media_mime_type,media_wa_type,media_size,media_name,media_hash,media_duration,origin,\
                latitude,longitude,thumb_image,remote_resource,received_timestamp,send_timestamp,receipt_server_timestamp,receipt_device_timestamp,\
                raw_data,recipient_count,media_caption,starred,read_device_timestamp,played_device_timestamp,participant_hash,quoted_row_id,mentioned_jids,\
                multicast_id,edit_version,media_enc_hash,payment_transaction_id,forwarded,preview_type,send_count) \
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
            loopcount = loopcount + 1
            bar.update(loopcount)
        tmp.execute("SELECT * FROM message_thumbnails")
        for row in tmp:
            reg = (row[0], row[1], row[2], row[3], row[4])
            msgstore.execute("INSERT INTO message_thumbnails VALUES(?,?,?,?,?)", reg)
            loopcount = loopcount + 1
            bar.update(loopcount)
        tmp.execute("SELECT * FROM message_media")
        for row in tmp:
            reg = (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17],\
                row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29], row[30], row[31], row[32], row[33], row[34])
            msgstore.execute("INSERT INTO message_media VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
            loopcount = loopcount + 1
            bar.update(loopcount)
        msg_quotes.clear()
        del msg_quotes
        #Key: old id, value: new_id
        keys_relationship = {}
        tmp.execute("SELECT old_id_messages, new_id_messages FROM keys_relationship")
        for row in tmp:
            try:
                keys_relationship[int(row[0])] = int(row[1])
            except:
                pass
        #At this point, old id references are changed to the new ones:
        #There are, sometimes, some inconsistencies caused by WhatsApp, so everything is wrapped inside a try/except block for avoiding blocks.
        #This block of code is not really elegant, but is reliable, quickly to write and it works just fine.
        msgstore.execute("SELECT display_message_row_id, last_message_row_id, last_read_message_row_id, last_read_receipt_sent_message_row_id FROM chat")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE chat SET display_message_row_id = ? WHERE display_message_row_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[1])], row[1])
                msgstore2.execute("UPDATE chat SET last_message_row_id = ? WHERE last_message_row_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[2])], row[2])
                msgstore2.execute("UPDATE chat SET last_read_message_row_id = ? WHERE last_read_message_row_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[3])], row[3])
                msgstore2.execute("UPDATE chat SET last_read_receipt_sent_message_row_id = ? WHERE last_read_receipt_sent_message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_table_id, last_read_message_table_id, last_read_receipt_sent_message_table_id, last_message_table_id FROM chat_list")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE chat_list SET message_table_id = ? WHERE message_table_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[1])], row[1])
                msgstore2.execute("UPDATE chat_list SET last_read_message_table_id = ? WHERE last_read_message_table_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[2])], row[2])
                msgstore2.execute("UPDATE chat_list SET last_read_receipt_sent_message_table_id = ? WHERE last_read_receipt_sent_message_table_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[3])], row[3])
                msgstore2.execute("UPDATE chat_list SET last_message_table_id = ? WHERE last_message_table_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT deleted_message_row_id, deleted_starred_message_row_id, deleted_categories_message_row_id, \
            deleted_categories_starred_message_row_id, deleted_message_categories FROM deleted_chat_job")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE deleted_chat_job SET deleted_message_row_id = ? WHERE deleted_message_row_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[1])], row[1])
                msgstore2.execute("UPDATE deleted_chat_job SET deleted_starred_message_row_id = ? WHERE deleted_starred_message_row_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[2])], row[2])
                msgstore2.execute("UPDATE deleted_chat_job SET deleted_categories_message_row_id = ? WHERE deleted_categories_message_row_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[3])], row[3])
                msgstore2.execute("UPDATE deleted_chat_job SET deleted_categories_starred_message_row_id = ? WHERE deleted_categories_starred_message_row_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[4])], row[4])
                msgstore2.execute("UPDATE deleted_chat_job SET deleted_message_categories = ? WHERE deleted_message_categories = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM labeled_messages")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE labeled_messages SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_ephemeral")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_ephemeral SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_forwarded")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_forwarded SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_future")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_future SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_future")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_future SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_group_invite")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_group_invite SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_link")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_link SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_location")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_location SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_media")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_media SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_media_interactive_annotation")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_media_interactive_annotation SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_mentions")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_mentions SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_payment")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_payment SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_payment_status_update")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_payment_status_update SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_payment_transaction_reminder")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_payment_transaction_reminder SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_product")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_product SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_quoted")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_quoted SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_quoted_group_invite")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_quoted_group_invite SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_quoted_group_invite_legacy")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_quoted_group_invite_legacy SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_quoted_location")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_quoted_location SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_quoted_media")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_quoted_media SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_quoted_mentions")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_quoted_mentions SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_quoted_product")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_quoted_product SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_quoted_text")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_quoted_text SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_quoted_vcard")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_quoted_vcard SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_revoked")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_revoked SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_send_count")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_send_count SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_streaming_sidecar")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_streaming_sidecar SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_system")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_system SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_system_block_contact")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_system_block_contact SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_system_chat_participant")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_system_chat_participant SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_system_device_change")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_system_device_change SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_system_ephemeral_setting_change")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_system_ephemeral_setting_change SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_system_group")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_system_group SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_system_number_change")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_system_number_change SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_system_photo_change")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_system_photo_change SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_system_value_change")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_system_value_change SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_template")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_template SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_template_button")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_template_button SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_template_quoted")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_template_quoted SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_text")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_text SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_thumbnail")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_thumbnail SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM message_vcard")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE message_vcard SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM messages_dehydrated_hsm")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE messages_dehydrated_hsm SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM messages_hydrated_four_row_template")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE messages_hydrated_four_row_template SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM messages_links")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE messages_links SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM messages_vcards")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE messages_vcards SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM messages_vcards_jids")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE messages_vcards_jids SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM missed_call_logs")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE missed_call_logs SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM pay_transaction")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE pay_transaction SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM quoted_message_product")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE quoted_message_product SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM receipt_device")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE receipt_device SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_row_id FROM receipt_user")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE receipt_user SET message_row_id = ? WHERE message_row_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_table_id, last_read_message_table_id, last_read_receipt_sent_message_table_id FROM status")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE status SET message_table_id = ? WHERE message_table_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[1])], row[1])
                msgstore2.execute("UPDATE status SET last_read_message_table_id = ? WHERE last_read_message_table_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[2])], row[2])
                msgstore2.execute("UPDATE status SET last_read_receipt_sent_message_table_id = ? WHERE last_read_receipt_sent_message_table_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        msgstore.execute("SELECT message_table_id, last_read_message_table_id, last_read_receipt_sent_message_table_id FROM status_list")
        for row in msgstore:
            try:
                reg = (keys_relationship[int(row[0])], row[0])
                msgstore2.execute("UPDATE status_list SET message_table_id = ? WHERE message_table_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[1])], row[1])
                msgstore2.execute("UPDATE status_list SET last_read_message_table_id = ? WHERE last_read_message_table_id = ?", reg)
            except:
                pass
            try:
                reg = (keys_relationship[int(row[2])], row[2])
                msgstore2.execute("UPDATE status_list SET last_read_receipt_sent_message_table_id = ? WHERE last_read_receipt_sent_message_table_id = ?", reg)
            except:
                pass
            loopcount = loopcount + 1
            bar.update(loopcount)
        db_msgstore.commit()
        msgstore.execute("PRAGMA synchronous = " + str(pragma_level))
        msgstore.execute("PRAGMA journal_mode = " + str(journal_mode))
        msgstore.execute("PRAGMA temp_store = " + str(temp_store_mode))
        db_msgstore.commit()
        for sql in fts_queries:
            msgstore.execute(sql)
        for sql in triggers_queries:
            msgstore.execute(sql)        
        db_msgstore.commit()
        triggers_queries.clear()
        fts_queries.clear()
        del triggers_queries
        del fts_queries
        db_temp.commit()
        db_temp.close()
        # try:
        #     os.remove("wa_sorting_data.db")
        # except:
        #     pass
        db_msgstore.close()
        keys_relationship.clear()
        del keys_relationship
    print("\nProcess finished correctly! Database optimization is suggested")
except KeyboardInterrupt:
    pass

#Optimize database at the end as well, as our writings fragmented it
try:
    print("During this script, a lot of modifications were done to the database. Running again the optimization procedure is recommended\
         for improving the database's operation after moving it back to the Android device\nPress Control-C if you want to finish and exit\n")
    optimize_database()
except KeyboardInterrupt:
    pass

getpass("\nScript finished! Thanks for using!\nPress ENTER to exit")

# SELECT NOT EXISTS (SELECT * FROM replies EXCEPT SELECT * FROM definitive_replies) AND NOT EXISTS (SELECT * FROM definitive_replies EXCEPT SELECT * FROM replies);
# msgstore.execute("CREATE TRIGGER IF NOT EXISTS _temporal_migration_trigger_ AFTER UPDATE ON messages_quotes BEGIN UPDATE messages SET quoted_row_id = new.quoted_row_id WHERE key_id=old.key_id; END")