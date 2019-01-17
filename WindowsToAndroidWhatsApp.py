## 2019 - This script can be located at github.com/ferferga

import os
import sqlite3
import progressbar
import sys
from getpass import getpass
import re

## VARIABLES AQUI
WPDBPath = ""
CallDB = ""
WPInsane = False

def WPDBConnection():
    try:
        conn = sqlite3.connect(WPDBPath)
        return conn        
    except sqlite3.OperationalError:
        print("ERROR 1: DATABASE OPERATION ERROR WITH WINDOWS DATABASE! Check that your database is valid and your writing permissions. Trying again...")
        WPDBConnection()
def TempDB():
    try:
        conn = sqlite3.connect("temp.db")
        return conn        
    except sqlite3.OperationalError:
        print("ERROR 1: DATABASE OPERATION ERROR WITH WINDOWS DATABASE! Check that your database is valid and your writing permissions. Trying again...")
        WPDBConnection()
def CallDBConnection():
    try:
        conn = sqlite3.connect(CallDB)        
        return conn        
    except sqlite3.OperationalError:
        print("ERROR 1.5: DATABASE OPERATION ERROR WITH WINDOWS DATABASE! Check that your database is valid and your writing permissions. Trying again...")
        CallDBConnection()
def ANDBConnection(first):
    try:
        conn = sqlite3.connect("msgstore.db")
        if first is True:
            print("\nCreated Android database successfully!")
        return conn        
    except sqlite3.OperationalError:
        print("ERROR 1: DATABASE OPERATION ERROR WITH ANDROID DATABASE! Check writing permissions... Trying again...")
        ANDBConnection(first)
def CheckSanityWPDB(database, calldb):
    print("Checking the databases for errors")
    tb = []
    try:
        db = database.cursor()
        cdb = calldb.cursor()
        db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for row in db:
            tb.append(row[0])
        if ("Messages" in tb) and ("Conversations" in tb) and ("CipherTextReceipts" in tb) and ("metadata" in tb) and ("MessageMiscInfos" in tb) and \
        ("LocalFiles" in tb) and ("PersistentActions" in tb) and ("EmojiUsages" in tb) and ("ReceiptState" in tb) and ("GroupParticipants" in tb) and \
        ("PostponedReceipts" in tb) and ("WaScheduledTasks" in tb) and ("EmojiSelectedIndexes" in tb) and ("ParticipantsHashJournal" in tb) and \
        ("JidInfos" in tb) and ("MessagesFts" in tb) and ("MessagesFts_segments" in tb) and ("MessagesFts_segdir" in tb) and ("MessagesFts_docsize" in tb) and \
        ("MessagesFts_stat" in tb) and ("ContactVCards" in tb) and ("FrequentChatScores" in tb) and ("WaStatuses" in tb) and ("PendingMessages" in tb) and \
        ("Stickers" in tb):
            print("\n'messages.db' is valid! Continuing...")
            tb.clear()
        else:
            getpass("'messages.db' is not a valid Windows Phone WhatsApp database. Press ENTER to close this program: ")
            sys.exit(0)
    except Exception as e:
        print("ERROR WHILE READING DATABASE 'messages.db': " + str(e))
        getpass("\nReport this error. The program is going to be closed now by pressing ENTER...")
        sys.exit(0)
    try:
        cdb = calldb.cursor()
        cdb.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for row in cdb:
            tb.append(row[0])
        if ("CallLog" in tb) and ("metadata" in tb):
            print("\n'calls.db' is valid! Continuing...")
            tb.clear()
        else:
            getpass("'messages.db' is not a valid Windows Phone WhatsApp database. Press ENTER to close this program: ")
            sys.exit(0)
    except Exception as e:
        print("ERROR WHILE READING DATABASE 'calls.db': " + str(e))
        getpass("\nReport this error. The program is going to be closed now by pressing ENTER...")
        sys.exit(0)
def CreateAndroidTables(database):
    try:
        print("Creating database structure...\n\n")
        with progressbar.ProgressBar(max_value=progressbar.UnknownLength) as bar:
            db = database.cursor()
            bar.update()
            db.execute("CREATE TABLE call_log_participant (_id INTEGER PRIMARY KEY AUTOINCREMENT, call_logs_row_id INTEGER, jid TEXT, call_result INTEGER)")
            db.execute("CREATE TABLE call_logs (_id INTEGER PRIMARY KEY AUTOINCREMENT, message_row_id INTEGER, transaction_id INTEGER, timestamp INTEGER, video_call INTEGER, duration INTEGER, call_result INTEGER, bytes_transferred INTEGER)")
            db.execute("CREATE TABLE chat_list (_id INTEGER PRIMARY KEY AUTOINCREMENT, key_remote_jid TEXT UNIQUE, message_table_id INTEGER, subject TEXT, creation INTEGER, last_read_message_table_id INTEGER, last_read_receipt_sent_message_table_id INTEGER, archived INTEGER, sort_timestamp INTEGER, mod_tag INTEGER, gen REAL, my_messages INTEGER, plaintext_disabled BOOLEAN, last_message_table_id INTEGER, unseen_message_count INTEGER, unseen_missed_calls_count INTEGER, unseen_row_count INTEGER, vcard_ui_dismissed INTEGER, deleted_message_id INTEGER, deleted_starred_message_id INTEGER, deleted_message_categories TEXT, change_number_notified_message_id INTEGER, last_important_message_table_id INTEGER, show_group_description INTEGER, unseen_earliest_message_received_time INTEGER)")
            db.execute("CREATE TABLE conversion_tuples (key_remote_jid TEXT PRIMARY KEY, data TEXT, source TEXT, last_interaction INTEGER, first_interaction INTEGER)")
            db.execute("CREATE TABLE deleted_chat_jobs (_id INTEGER PRIMARY KEY AUTOINCREMENT, key_remote_jid TEXT NOT NULL, block_size INTEGER, deleted_message_id INTEGER, deleted_starred_message_id INTEGER, deleted_message_categories TEXT, delete_files BOOLEAN)")
            db.execute("CREATE TABLE frequents (_id INTEGER PRIMARY KEY AUTOINCREMENT, jid TEXT NOT NULL, type INTEGER NOT NULL, message_count INTEGER NOT NULL)")
            bar.update()
            db.execute("CREATE TABLE group_participants (_id INTEGER PRIMARY KEY AUTOINCREMENT, gjid TEXT NOT NULL, jid TEXT NOT NULL, admin INTEGER, pending INTEGER, sent_sender_key INTEGER)")
            db.execute("CREATE TABLE group_participants_history (_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME NOT NULL, gjid TEXT NOT NULL, jid TEXT NOT NULL, action INTEGER NOT NULL, old_phash TEXT NOT NULL, new_phash TEXT NOT NULL)")
            db.execute("CREATE TABLE jid ( _id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, server TEXT NOT NULL, agent INTEGER, type INTEGER, raw_string TEXT)")
            db.execute("CREATE TABLE labeled_jids (_id INTEGER PRIMARY KEY AUTOINCREMENT, label_id INTEGER NOT NULL, jid TEXT)")
            db.execute("CREATE TABLE labeled_messages (_id INTEGER PRIMARY KEY AUTOINCREMENT, label_id INTEGER NOT NULL, message_row_id INTEGER NOT NULL)")
            db.execute("CREATE TABLE labels (_id INTEGER PRIMARY KEY AUTOINCREMENT, label_name TEXT, predefined_id INTEGER, color_id INTEGER)")            
            bar.update()
            db.execute("CREATE TABLE media_refs (_id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT UNIQUE, ref_count INTEGER)")
            db.execute("CREATE TABLE media_streaming_sidecar (_id INTEGER PRIMARY KEY AUTOINCREMENT, sidecar BLOB, key_remote_jid TEXT NOT NULL, key_from_me INTEGER, key_id TEXT NOT NULL, timestamp datetime)")
            db.execute("CREATE TABLE message_thumbnails (thumbnail BLOB, timestamp DATETIME, key_remote_jid TEXT NOT NULL, key_from_me INTEGER, key_id TEXT NOT NULL)")
            db.execute("CREATE TABLE messages (_id INTEGER PRIMARY KEY AUTOINCREMENT, key_remote_jid TEXT NOT NULL, key_from_me INTEGER, key_id TEXT NOT NULL, status INTEGER, needs_push INTEGER, data TEXT, timestamp INTEGER, media_url TEXT, media_mime_type TEXT, media_wa_type TEXT, media_size INTEGER, media_name TEXT, media_hash TEXT, media_duration INTEGER, origin INTEGER, latitude REAL, longitude REAL, thumb_image TEXT, remote_resource TEXT, received_timestamp INTEGER, send_timestamp INTEGER, receipt_server_timestamp INTEGER, receipt_device_timestamp INTEGER, raw_data BLOB, recipient_count INTEGER, read_device_timestamp INTEGER, played_device_timestamp INTEGER, media_caption TEXT, participant_hash TEXT, starred INTEGER, quoted_row_id INTEGER, mentioned_jids TEXT, multicast_id TEXT, edit_version INTEGER, media_enc_hash TEXT, payment_transaction_id TEXT, forwarded INTEGER, preview_type INTEGER, send_count INTEGER)")
            db.execute("CREATE TABLE messages_dehydrated_hsm (_id INTEGER PRIMARY KEY AUTOINCREMENT, message_row_id INTEGER UNIQUE, message_elementname TEXT, message_namespace TEXT, message_lg TEXT)")
            db.execute("CREATE TABLE messages_edits (_id INTEGER PRIMARY KEY AUTOINCREMENT, key_remote_jid TEXT NOT NULL, key_from_me INTEGER, key_id TEXT NOT NULL, status INTEGER, needs_push INTEGER, data TEXT, timestamp INTEGER, media_url TEXT, media_mime_type TEXT, media_wa_type TEXT, media_size INTEGER, media_name TEXT, media_caption TEXT, media_hash TEXT, media_duration INTEGER, origin INTEGER, latitude REAL, longitude REAL, thumb_image TEXT, remote_resource TEXT, received_timestamp INTEGER, send_timestamp INTEGER, receipt_server_timestamp INTEGER, receipt_device_timestamp INTEGER, read_device_timestamp INTEGER, played_device_timestamp INTEGER, raw_data BLOB, recipient_count INTEGER, participant_hash TEXT, starred INTEGER, quoted_row_id INTEGER, mentioned_jids TEXT, multicast_id TEXT, edit_version INTEGER, media_enc_hash TEXT, payment_transaction_id TEXT, forwarded INTEGER, preview_type INTEGER, send_count INTEGER)")
            db.execute("CREATE VIRTUAL TABLE messages_fts USING FTS3()")
            bar.update()
            #db.execute("CREATE TABLE messages_fts_content (docid INTEGER PRIMARY KEY, 'c0content')")
            #db.execute("CREATE TABLE messages_fts_segdir (level INTEGER,idx INTEGER,start_block INTEGER,leaves_end_block INTEGER,end_block INTEGER,root BLOB,PRIMARY KEY(level, idx))")
            #db.execute("CREATE TABLE messages_fts_segments (blockid INTEGER PRIMARY KEY, block BLOB)")
            db.execute("CREATE TABLE messages_links (_id INTEGER PRIMARY KEY AUTOINCREMENT, key_remote_jid TEXT, message_row_id INTEGER, link_index INTEGER)")
            db.execute("CREATE TABLE messages_quotes (_id INTEGER PRIMARY KEY AUTOINCREMENT, key_remote_jid TEXT NOT NULL, key_from_me INTEGER, key_id TEXT NOT NULL, status INTEGER, needs_push INTEGER, data TEXT, timestamp INTEGER, media_url TEXT, media_mime_type TEXT, media_wa_type TEXT, media_size INTEGER, media_name TEXT, media_caption TEXT, media_hash TEXT, media_duration INTEGER, origin INTEGER, latitude REAL, longitude REAL, thumb_image TEXT, remote_resource TEXT, received_timestamp INTEGER, send_timestamp INTEGER, receipt_server_timestamp INTEGER, receipt_device_timestamp INTEGER, read_device_timestamp INTEGER, played_device_timestamp INTEGER, raw_data BLOB, recipient_count INTEGER, participant_hash TEXT, starred INTEGER, quoted_row_id INTEGER, mentioned_jids TEXT, multicast_id TEXT, edit_version INTEGER, media_enc_hash TEXT, payment_transaction_id TEXT, forwarded INTEGER, preview_type INTEGER, send_count INTEGER)")
            db.execute("CREATE TABLE messages_vcards (_id INTEGER PRIMARY KEY AUTOINCREMENT, message_row_id INTEGER, sender_jid TEXT, vcard TEXT, chat_jid TEXT)")
            db.execute("CREATE TABLE messages_vcards_jids (_id INTEGER PRIMARY KEY AUTOINCREMENT, message_row_id INTEGER, vcard_jid TEXT, vcard_row_id INTEGER)")
            db.execute("CREATE TABLE missed_call_log_participant (_id INTEGER PRIMARY KEY AUTOINCREMENT, call_logs_row_id INTEGER, jid TEXT, call_result INTEGER)")
            db.execute("CREATE TABLE missed_call_logs (_id INTEGER PRIMARY KEY AUTOINCREMENT, message_row_id INTEGER, timestamp INTEGER, video_call INTEGER)")
            bar.update()
            db.execute("CREATE TABLE pay_transactions (key_remote_jid TEXT, key_from_me INTEGER, key_id TEXT, id TEXT, timestamp INTEGER, status INTEGER, error_code TEXT, sender TEXT, receiver TEXT, type INTEGER, currency TEXT, amount_1000, credential_id TEXT, methods TEXT, bank_transaction_id TEXT, metadata TEXT, init_timestamp INTEGER, request_key_id TEXT, country TEXT, version INTEGER, future_data BLOB)")
            db.execute("CREATE TABLE props (_id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE, value TEXT)")
            db.execute("CREATE TABLE receipts (_id INTEGER PRIMARY KEY AUTOINCREMENT, key_remote_jid TEXT NOT NULL, key_id TEXT NOT NULL, remote_resource TEXT, receipt_device_timestamp INTEGER, read_device_timestamp INTEGER, played_device_timestamp INTEGER)")
            #db.execute("CREATE TABLE sqlite_sequence(name,seq)")
            db.execute("CREATE TABLE status_list (_id INTEGER PRIMARY KEY AUTOINCREMENT, key_remote_jid TEXT UNIQUE, message_table_id INTEGER, last_read_message_table_id INTEGER, last_read_receipt_sent_message_table_id INTEGER, timestamp INTEGER, unseen_count INTEGER, total_count INTEGER, first_unread_message_table_id INTEGER, autodownload_limit_message_table_id INTEGER)")
            db.execute("CREATE UNIQUE INDEX call_log_participants_key_index on call_log_participant (call_logs_row_id, jid)")
            db.execute("CREATE UNIQUE INDEX call_logs_key_index on call_logs (message_row_id, transaction_id)")
            bar.update()
            db.execute("CREATE INDEX deleted_chat_jobs_index ON deleted_chat_jobs (key_remote_jid, _id)")
            db.execute("CREATE INDEX group_participants_history_index on group_participants_history (gjid)")
            db.execute("CREATE UNIQUE INDEX group_participants_index on group_participants (gjid, jid)")
            db.execute("CREATE UNIQUE INDEX jid_key_index ON jid ( user, server, agent)")
            db.execute("CREATE UNIQUE INDEX jid_raw_string_index ON jid ( raw_string)")
            bar.update()
            db.execute("CREATE UNIQUE INDEX labeled_jids_index on labeled_jids (label_id, jid)")
            db.execute("CREATE UNIQUE INDEX labeled_messages_index on labeled_messages (label_id, message_row_id)")
            db.execute("CREATE UNIQUE INDEX labels_index ON labels (label_name)")
            db.execute("CREATE INDEX media_hash_index on messages (media_hash)")
            db.execute("CREATE INDEX media_type_index on messages (media_wa_type)")
            db.execute("CREATE INDEX media_type_jid_index on messages (key_remote_jid, media_wa_type)")
            bar.update()
            db.execute("CREATE UNIQUE INDEX message_payment_transactions_id_index ON pay_transactions (id)")
            db.execute("CREATE UNIQUE INDEX message_payment_transactions_index ON pay_transactions (key_id)")
            db.execute("CREATE INDEX messages_jid_id_index on messages (key_remote_jid, _id)")
            db.execute("CREATE UNIQUE INDEX messages_key_index on messages (key_remote_jid, key_from_me, key_id)")
            db.execute("CREATE UNIQUE INDEX messages_thumbnail_key_index on message_thumbnails (key_remote_jid, key_from_me, key_id)")
            db.execute("CREATE UNIQUE INDEX missed_call_log_participants_key_index on missed_call_log_participant (call_logs_row_id, jid)")
            bar.update()
            db.execute("CREATE UNIQUE INDEX missed_call_logs_key_index on missed_call_logs (message_row_id)")
            db.execute("CREATE INDEX receipts_key_index on receipts (key_remote_jid, key_id)")
            db.execute("CREATE INDEX starred_index on messages (starred)")
            db.execute("CREATE TRIGGER call_logs_bd_for_call_log_participants_trigger BEFORE DELETE ON call_logs BEGIN DELETE FROM call_log_participant WHERE call_logs_row_id=old._id; END")
            db.execute("CREATE TRIGGER labels_bd_for_labeled_jids_trigger BEFORE DELETE ON labels BEGIN DELETE FROM labeled_jids WHERE label_id=old._id; END")
            db.execute("CREATE TRIGGER labels_bd_for_labeled_messages_trigger BEFORE DELETE ON labels BEGIN DELETE FROM labeled_messages WHERE label_id=old._id; END")
            bar.update()
            db.execute("CREATE TRIGGER messages_bd_for_call_logs_trigger BEFORE DELETE ON messages BEGIN DELETE FROM call_logs WHERE message_row_id=old._id; END")
            db.execute("CREATE TRIGGER messages_bd_for_dehydrated_hsms_trigger BEFORE DELETE ON messages BEGIN DELETE FROM messages_dehydrated_hsm WHERE message_row_id=old._id; END")
            db.execute("CREATE TRIGGER messages_bd_for_labeled_messages_trigger BEFORE DELETE ON messages BEGIN DELETE FROM labeled_messages WHERE message_row_id=old._id; END")
            db.execute("CREATE TRIGGER messages_bd_for_links_trigger BEFORE DELETE ON messages BEGIN DELETE FROM messages_links WHERE message_row_id=old._id; END")
            db.execute("CREATE TRIGGER messages_bd_for_missed_call_logs_trigger BEFORE DELETE ON messages BEGIN DELETE FROM missed_call_logs WHERE message_row_id=old._id; END")
            db.execute("CREATE TRIGGER messages_bd_for_quotes_trigger BEFORE DELETE ON messages BEGIN DELETE FROM messages_quotes WHERE _id=old.quoted_row_id; END")
            bar.update()
            db.execute("CREATE TRIGGER messages_bd_for_receipts_trigger BEFORE DELETE ON messages BEGIN DELETE FROM receipts WHERE key_remote_jid=old.key_remote_jid AND key_id=old.key_id; END")
            db.execute("CREATE TRIGGER messages_bd_for_vcards_jids_trigger BEFORE DELETE ON messages BEGIN DELETE FROM messages_vcards_jids WHERE message_row_id=old._id; END")
            db.execute("CREATE TRIGGER messages_bd_for_vcards_trigger BEFORE DELETE ON messages BEGIN DELETE FROM messages_vcards WHERE message_row_id=old._id; END")
            db.execute("CREATE TRIGGER messages_bd_trigger BEFORE DELETE ON messages BEGIN DELETE FROM messages_fts WHERE docid=old._id; END")
            db.execute("CREATE TRIGGER missed_call_logs_bd_for_missed_call_log_participants_trigger BEFORE DELETE ON missed_call_logs BEGIN DELETE FROM missed_call_log_participant WHERE call_logs_row_id=old._id; END")
            bar.update()
            database.commit()
            bar.update()
        print("\nCreated Android database structure successfully")
    except sqlite3.OperationalError as e:
        print("ERROR WHILE CREATING THE DATABASE! THERE MIGHT BE ANOTHER MSGSTORE.DB FILE IN YOUR WORKING DIRECTORY. ERROR INFO:")
        print(str(e))
        getpass("The program can't continue. Press ENTER to exit")
        sys.exit(0)

def MoveDB():
    OriginalIDs = []
    NewIDs = []
    QuoteMsg = []
    QuotedID = []
    WPMessageCount = 0
    WPChatCount = 0
    WPCallsCount = 0
    WPContactCount = 0
    print("\nStarting to merge the databases! Preparing the data...")
    AndroidDatabase = ANDBConnection(False)
    WindowsDatabase = WPDBConnection()
    try:
        os.remove("temp.db")
    except:
        pass
    RepliesDB = TempDB()
    tmpdb = RepliesDB.cursor()
    wpdb = WindowsDatabase.cursor()
    andb = AndroidDatabase.cursor()
    calldb = CallDBConnection().cursor()
    calldb.execute('SELECT * FROM CallLog')
    for row in calldb:
        WPCallsCount = WPCallsCount + 1
    print("There are "+ str(WPCallsCount) + " calls in WP database")
    print("\n\nTransferring calls logs...")
    try:        
        with progressbar.ProgressBar(max_value=WPCallsCount) as bar:
            LoopCount = 0
            calldb.execute('SELECT * FROM CallLog')
            for row in calldb:
                LoopCount = LoopCount + 1
                if row[10] is None:
                    video_call = 0
                else:
                    video_call = 1
                duration = row[6] - row[4]
                DataUsage = row[8] + row[9]
                reg1 = (None, row[1], row[3], "call:" + row[2], 6, 0, None, row[4], None, None, 8, 0, None, None, 0, 0, 0.0, 0.0, None, None, row[5], -1, -1, -1, None, 0, None, None, None, None, None, 0, None, None, 0, None, None, 0, 0, None)
                andb.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg1)
                if row[5] is None:
                    ins = (None, LoopCount, row[4], video_call)
                    andb.execute("INSERT INTO missed_call_logs VALUES(?,?,?,?)", ins)
                else:
                    insert = (None, LoopCount, int(-1), row[4], video_call, duration, row[7], DataUsage)
                    andb.execute("INSERT INTO call_logs VALUES(?,?,?,?,?,?,?,?)", insert)
                bar.update(LoopCount)  
        print("\n\nFinished! Writing changes to disk...")
        AndroidDatabase.commit()
    except Exception as e:
        print("\nERROR WHILE MOVING CALLS!: " + str(e))
        print("\n\nThere is no way to continue. Discard 'msgstore.db' inmediately. Report this error")
        getpass("Press ENTER to exit now...")
        sys.exit(0)
    print("\nNow processing some of WA's metadata...")
    try:
        with progressbar.ProgressBar(max_value=progressbar.UnknownLength) as bar:
            wpdb.execute('SELECT * FROM JidInfos')
            ProgressBarVal = 0
            for row in wpdb:
                user, server = row[1].split("@")
                if server == "g.us":
                    jidtype = 1
                elif server == "broadcast" and user == "status":
                    jidtype = 5
                else:
                    jidtype = 0
                insert = (None, user, server, 0, jidtype, row[1])
                andb.execute("INSERT INTO jid VALUES(?,?,?,?,?,?)", insert)
                bar.update()
            wpdb.execute('SELECT * FROM GroupParticipants')
            for row in wpdb:
                insert = (None, row[1], row[2], 0, 0, 0)
                try:
                    andb.execute("INSERT INTO group_participants VALUES(?,?,?,?,?,?)", insert)
                except:
                    pass
                ProgressBarVal = ProgressBarVal + 1
                bar.update(ProgressBarVal)
    except Exception as e:
        print("\nERROR WHILE PROCESSING METADATA!: " + str(e))
        print("\n\nThere is no way to continue. Discard 'msgstore.db' inmediately. Report this error")
        getpass("\nPress ENTER to exit now...")
        sys.exit(0)
    print("\nCommiting changes to the disk...")
    AndroidDatabase.commit()
    print("\nNow processing messages...")
    wpdb.execute('SELECT Data FROM Messages')
    for row in wpdb:
        WPMessageCount = WPMessageCount + 1
    print("There are " + str(WPMessageCount) + " messages in this WP Database")
    print("\n\nProcessing some messages metadata before moving them... This might take some time...\n")
    tmpdb.execute("CREATE TABLE replies (quote_msg_id INTEGER PRIMARY KEY, quote_key_id TEXT, quoted_key_id TEXT, quoted_msg_id INTEGER)")
    tmpdb.execute("CREATE TABLE definitive_replies (quote_msg_id INTEGER PRIMARY KEY, quote_key_id TEXT, quoted_key_id TEXT, quoted_msg_id INTEGER)")
    RepliesDB.commit()
    with progressbar.ProgressBar(max_value=WPMessageCount) as bar:
        wpdb.execute('SELECT * FROM Messages')
        BarCount5 = 0
        for rc in wpdb:
            if rc[37] is not None:
                st1 = str(rc[37])
                st = st1.replace("\\n", "-ç")
                st = st.replace("\\x", "_¨")
                quote_key = re.findall(r"(?<=\-ç_¨[1-9][1-9])(.*?)(?=\_¨12_¨1a34)", st)
                if quote_key:
                    if not (len(quote_key[0]) == 18 or len(quote_key) == 30 or len(quote_key) == 32):
                        if "-ç_¨12" in quote_key[0]:
                            trash, useful = quote_key[0].split("-ç_¨12")
                        elif "-ç_¨1e" in quote_key[0]:
                            trash, useful = quote_key[0].split("-ç_¨1e")
                        elif "-ç_¨14" in quote_key[0]:
                            trash, useful = quote_key[0].split("-ç_¨14")
                        elif "-ç_¨1e" in quote_key[0]:
                            trash, useful = quote_key[0].split("-ç_¨1e")
                        else:
                            useful = None
                        jid_key = useful
                    else:
                        jid_key = quote_key[0]                        
                else:
                    jid_key = None
                if jid_key is not None:
                    QuoteMsg.append(rc[0])
                    wpdb3 = WindowsDatabase.cursor()
                    wpdb3.execute("SELECT MessageID FROM Messages WHERE KeyId = '" + jid_key + "'")
                    for rd in wpdb3:
                        QuotedID.append(rd[0])
                        ins7 = (rc[0], rc[3], jid_key, rd[0])
                        tmpdb.execute("INSERT INTO replies VALUES(?,?,?,?)", ins7)
            BarCount5 = BarCount5 + 1                
            bar.update(BarCount5)
    RepliesDB.commit()
    print("\n\nMessages' metadata processed! Now moving messages...\n")
    try:
        with progressbar.ProgressBar(max_value=WPMessageCount) as bar:
            IDToCommit = 0
            ProgressBarVal = 0
            QuotedKeyID = []
            QuoteID = 0
            andb.execute('SELECT _id FROM messages ORDER BY _id DESC LIMIT 1')
            for ro in andb:
                IDToCommit = ro[0] + 1
            wpdb.execute('SELECT * FROM Messages')
            for row in wpdb:
                thumb_image = None
                wpdb2 = WindowsDatabase.cursor()
                wpdb2.execute("SELECT ImageBinaryInfo FROM MessageMiscInfos WHERE MessageId = '" + str(row[0]) + "'")
                for row2 in wpdb2:
                    thumb_image = row2[0]
                if thumb_image is not None:
                    inst = (thumb_image, row[10], row[1], row[2], row[3])
                    andb.execute("INSERT INTO message_thumbnails VALUES(?,?,?,?,?)", inst)
                mentioned_jids = None
                OriginalIDs.append(row[0])
                NewIDs.append(IDToCommit)
                if row[7] is not None:                    
                    if "@34" in row[7]:
                        mentions = re.findall(r"\b@34\w+", row[7])
                        if mentions is not None:
                            mentions = ""
                            for men in mentions:
                                men.replace("@", "")
                                if LoopC == 0:
                                    mentioned_jids = (mentioned_jids + men + "@s.whatsapp.net")
                                else:
                                    mentioned_jids = (mentioned_jids + "," + men + "s.whatsapp.net")
                                LoopC = LoopC + 1
                reg = (IDToCommit, row[1], row[2], row[3], row[4], 0, row[7], int(str(str(row[10]) + "000")), row[13], row[15], row[16], row[17], row[20], None, row[18], row[19], row[24], row[25], thumb_image, row[5], int(str(str(row[10] + 10) + "000")), -1, -1, -1, row[8], None, int(str(str(row[10] + 12) + "000")), None, row[22], row[34], row[35], 0, mentioned_jids, None, None, None, None, None, None, None)
                if row[0] in QuotedID:
                    andb.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
                    rego = (None, row[1], row[2], row[3], row[4], 0, row[7], int(str(str(row[10]) + "000")), row[13], row[15], row[16], row[17], None, row[22], None, row[18], row[19], row[24], row[25], thumb_image, row[5], int(str(str(row[10] + 10) + "000")), -1, -1, -1, None, None, row[8], 0, row[34], row[35], 0, mentioned_jids, None, 0, None, None, None, None, None)
                    andb.execute("INSERT INTO messages_quotes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rego)
                else:
                    andb.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
                IDToCommit = IDToCommit + 1
                ProgressBarVal = ProgressBarVal + 1
                bar.update(ProgressBarVal)
        print("\nMoved all the messages successfully! Writing the changes into the database... This might take a while if you had many messages!\n")
        AndroidDatabase.commit()
        print("\n\Doing the finishing touches with the messages...\n")
        with progressbar.ProgressBar(max_value=progressbar.UnknownLength) as bar:
            andb.execute("SELECT * FROM messages_quotes")
            for rk in andb:
                tmpdb2 = RepliesDB.cursor()
                tmpdb2.execute("SELECT * FROM replies WHERE quoted_key_id ='" + rk[3] + "'")
                for rt in tmpdb2:
                    inj = (rt[0], rt[1], rt[2], rt[3])
                    tmpdb.execute("INSERT INTO definitive_replies VALUES(?,?,?,?)", inj)
                    bar.update()
            RepliesDB.commit()
            andb2 = AndroidDatabase.cursor()
            andb3 = AndroidDatabase.cursor()
            tmpdb.execute("SELECT * FROM definitive_replies")
            for rg in tmpdb:
                andb.execute("SELECT _id FROM messages_quotes WHERE key_id = '" + rg[2] + "'")
                for column in andb:
                    quote_id = column[0]
                    try:
                        andb2.execute("UPDATE messages SET quoted_row_id = '" + str(quote_id) + "' WHERE _id = '" + str(NewIDs[OriginalIDs.index(rg[0])]) + "'")
                    except:
                        continue
                    try:
                        rn = (quote_id, rg[1])
                        andb2.execute("UPDATE messages_quotes SET quoted_row_id = '" + str(quote_id) + "' WHERE key_id = '" + rg[1] + "'")
                    except:
                        pass
                bar.update()
        print("\nAll finished with the messages! Writing changes into the disk...")
        AndroidDatabase.commit()
        QuoteMsg.clear()
        QuotedID.clear()
    except Exception as e:
        getpass("\nERROR WHILE MOVING MESSAGES!: " + str(e) + "\n\nReport this problem. The program can't continue, so discard 'msgstore.db' inmediately.\nExit by pressing ENTER...")
        sys.exit(0)
    print("\n\nNow transferring chats...")
    wpdb.execute('SELECT ConversationID FROM Conversations')
    for row in wpdb:
        WPChatCount = WPChatCount + 1
    print("There are " + str(WPChatCount) + " chats in this WP Database")
    print("\n\nMoving conversations table...")
    try:
        with progressbar.ProgressBar(max_value=WPChatCount) as bar:
            wpdb.execute("SELECT * FROM Conversations")
            for row in wpdb:
                if row[11] is not None:
                    try:
                        ind = OriginalIDs.index(row[11])
                    except:
                        continue
                    LastMessage = NewIDs[ind]
                else:
                    LastMessage = None
                if row[14] is not None:
                    wpdb2 = WindowsDatabase.cursor()
                    wpdb2.execute("SELECT MessageID FROM Messages WHERE KeyRemoteJid = '" + row[1] + "' ORDER BY MessageID DESC LIMIT 1")
                    for row4 in wpdb2:
                        index = OriginalIDs.index(row4[0])
                    LastUnreadMessage = NewIDs[index]
                else:
                    LastUnreadMessage = None
                if row[13] is not None:
                    wpdb3 = WindowsDatabase.cursor()
                    wpdb3.execute("SELECT TimestampLong FROM Messages WHERE MessageID = '" + str(row[14]) + "'")
                    for row2 in wpdb2:
                        unseen_time = int(str(row[0] + "000"))
                else:
                    unseen_time = None
                insert = (None, row[1], LastMessage, row[6], row[5], LastUnreadMessage, LastUnreadMessage, None, row[3], row[22], None, 1, True, LastMessage, row[13], None, row[13], None, None, None, None, None, None, None, unseen_time)
                andb.execute("INSERT INTO chat_list VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", insert)
    except Exception as e:
        print("\nERROR WHILE MOVING CONVERSATIONS OVERVIEW!: " + str(e))
        print("\n\nThere is no way to continue. Discard 'msgstore.db' inmediately. Report this error")
        getpass("Press ENTER to exit now...")
        sys.exit(0)
    print("\nDone! Writing changes to disk...")
    AndroidDatabase.commit()
    print("\n\nNow transferring contacts' ...")
    wpdb.execute("SELECT VCardId FROM ContactVCards")
    for row in wpdb:
        WPContactCount = WPContactCount + 1
    print("\nYou have sent " + str(WPContactCount) + " contacts through WhatsApp!")
    print("\n")
    try:
        with progressbar.ProgressBar(max_value=WPContactCount) as bar:
            LoopNumber = 0
            wpdb.execute("SELECT * FROM ContactVCards")
            for row in wpdb:
                try:                    
                    index = OriginalIDs.index(row[2])
                except:
                    continue
                wpdb2 = WindowsDatabase.cursor()
                wpdb2.execute("SELECT * FROM Messages WHERE MessageID = '" + str(row[2]) + "'")
                for rb in wpdb2:
                    data = rb[7]                    
                    sender_jid = rb[1]
                if data is None:
                    continue
                ins = (None, NewIDs[index], row[1], data, sender_jid)
                andb.execute("INSERT INTO messages_vcards VALUES(?,?,?,?,?)", ins)
                contact_jid = re.findall(r"(?<=\waid=)(.*?)(?=\:)", data)
                LoopNumber = LoopNumber + 1
                ins2 = (None, NewIDs[index], contact_jid[0] + "@s.whatsapp.net", LoopNumber)
                andb.execute("INSERT INTO messages_vcards_jids VALUES(?,?,?,?)", ins2)
    except Exception as e:
        print("\nERROR WHILE MOVING CONTACTS!: " + str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("\n")
        print(exc_type, fname, exc_tb.tb_lineno)
        print("\n\nThere is no way to continue. Discard 'msgstore.db' inmediately. Report this error")
        getpass("Press ENTER to exit now...")
        sys.exit(0)
    AndroidDatabase.commit()
    print("\nCleaning the database...")
    AndroidDatabase.execute("VACUUM")
    AndroidDatabase.close()
    print("\nEverything has been done correctly! Thank you for using this tiny script made by ferferga!")
    getpass("\n\nPress ENTER to close...\n ")
    sys.exit(0)
    

## PUNTO DE INICIO DEL CÓDIGO
print("\n== MOVE WHATSAPP FROM WINDOWS PHONE TO ANDROID == (a script made by ferferga)\n")
while True:
    print()
    WPDBPath = input("Please, drag and drop your WhatsApp's Windows database (messages.db) file here: ")
    if "messages.db" not in WPDBPath:
        print("\nIncorrect file type. Try again...")
    else:
        break

while True:
    print()
    CallDB = input("Now, please, drag and drop 'calls.db' file here: ")
    if "calls.db" not in CallDB:
        print("\nIncorrect file type. Try again...")
    else:
        break

CheckSanityWPDB(WPDBConnection(), CallDBConnection())
getpass("\nRemove any Android backup (msgstore.db) from your working directory, it will be replaced with a version made by this script. Press ENTER to continue: ")
try:
    os.remove("msgstore.db")
except:
    pass
CreateAndroidTables(ANDBConnection(True))
try:
    getpass("\nEverything is ready for moving your messages over to Android. Press CTRL + C to cancel, otherwise press ENTER to continue: ")
except:
    print("\n\nGoodbye! You can start this program again whenever you feel ready!")
    os.remove("msgstore.db")
    sys.exit(0)
MoveDB()