import sqlite3

conn = sqlite3.connect('user.db')
curs = conn.cursor()
curs.execute(
    "CREATE TABLE IF NOT EXISTS activity (activity_name text PRIMARY KEY, motors text, duration text, intensity text)") 

cnt = 1

for rhythm in range(1,4):
    motor_arr = []
    if rhythm == 1:
        motor_arr.append(0)
    elif rhythm == 2:
        motor_arr.extend([1,2,3,4])
    else:
        motor_arr.extend([1,4,1,4])
    
    for duration in range(1,4):
        dur_arr = []
        if (rhythm == 1):
            dur_arr.append(duration)
        else:
            dur_arr.extend([duration]*4)
        for intensity in range(1,4):
            int_arr = []
            if(rhythm == 1):
                int_arr.append(intensity)
            else:
                int_arr.extend([intensity]*4)
            

            str_motors = ",".join([str(k) for k in motor_arr])
            str_duration = ",".join([str(k) for k in dur_arr])
            str_intensity = ",".join([str(k) for k in int_arr])
            actv_name = "Stimuli " + str(cnt)
            cnt += 1
            # print(str_motors)
            # print(str_duration)
            # print(str_intensity)
            # print(str_motors+"s"+str_duration+"s"+str_intensity)


            curs.execute("INSERT INTO activity VALUES (:activity_name, :motors, :duration, :intensity)",
                                 {
                                     'activity_name': str(actv_name),
                                     'motors': str(str_motors),
                                     'duration': str(str_duration),
                                     'intensity':str(str_intensity)
                                 })

# conn.commit()
# conn.close()

