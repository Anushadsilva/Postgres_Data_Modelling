import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    # open song file
    df = pd.read_json(filepath, lines = True)
    
    # insert song record
    song_data = df.loc[0,['song_id','title','artist_id','year','duration']].values.tolist()
    song_data[3] = int(song_data[3])
    #print(song_data[3])
    cur.execute(song_table_insert, song_data)
    
    # insert artist record
    artist_data = df.loc[0,['artist_id','artist_name','artist_location','artist_latitude','artist_longitude']].values.tolist()
    cur.execute(artist_table_insert, artist_data)



def process_log_file(cur, filepath):
    # open log file
    df = pd.read_json(filepath, lines = True)

    # filter by NextSong action
    df = df[df.page=='NextSong']

    # convert timestamp column to datetime
    t = df['ts'].astype('datetime64[ms]')
    
    
    # insert time data records
    time_data = list(zip(t.tolist(),t.dt.hour.tolist(),t.dt.day.tolist(),t.dt.week.tolist(),t.dt.month.tolist(),t.dt.year.tolist(),\
             t.dt.weekday.tolist()))
    #print(time_data)
    column_labels = ['timestampe','hour','day','week','month','year','weekday']
    time_df = pd.DataFrame(time_data, columns = column_labels)


    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df =  df.loc[:,['userId','firstName','lastName','gender','level']]
    #print(user_df )


    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        songplay_data = (index, t[index],row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
        #print(songplay_data)
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            print(f)
            print(os.path.abspath(f))
            all_files.append(os.path.abspath(f))
           #break;

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    """
    - Establishes connection with the sparkify database and gets
    cursor to it.  
    
    - Description:  process_data -This function can be used to read the file in the filepath (data/song_data)
      to get all the songs and populate songs and artists records.  
    
    - Description:  process_data -This function can be used to read the file in the filepath (data/log_data)
      to get the user and time info and used to populate the users and time dim tables.
    
    - Finally, closes the connection. 
    """
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()
    process_data(cur, conn, filepath='data/song_data', func=process_song_file)   
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)
    conn.close()
 
if __name__ == "__main__":
    main()