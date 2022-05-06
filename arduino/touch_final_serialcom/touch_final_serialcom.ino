const int PIN_1   = 5;
const int PIN_2   = 6;
const int PIN_3   = 9;
const int PIN_4   = 10;

const int FSR_ANALOG_PIN = 1; 
const int FSR_THRESHOLD = 5;
const int VIBR_DELAY = 300;
const int MAX_MESSAGE_SIZE = 10;

const int MESSAGE_DELAY = 1500;

int fsr_in;
int fsr_out; 
String data_in;

//void handle_message(String data)
//{
//  int segment_array[4] = {PIN_1, PIN_2, PIN_3, PIN_4};
//  int motor_array[MAX_MESSAGE_SIZE] = {0,0,0,0,0,0,0,0,0,0};
//  int time_array[MAX_MESSAGE_SIZE]  = {0,0,0,0,0,0,0,0,0,0};
//
//  int data_len = data.length();
//  int half_len = data_len/2;
//  
//  if (data_len%2 == 0 and data[0] == 'm' and data[half_len] == 's')
//  {
//    for(int pos = 1; pos < data_len; pos++)
//    {
//      if ( pos < half_len ) 
//        motor_array[pos-1] = ((int)data[pos]-48);
//      else if ( pos == half_len ) 
//        continue;
//      else 
//        time_array[pos - (half_len+1)] = ((int)data[pos]-48) * 100;
//    }
//
//    int motor_no = half_len - 1;
//    int cnt = 0;
//    
//    while (cnt < motor_no)
//    {   
//      analogWrite(segment_array[motor_array[cnt]-1], 255);
//      delay(1500);
//      analogWrite(segment_array[motor_array[cnt]-1], 0);
//      cnt++;
//    }
//  } 
//}



void handle_message(String data)
{
  int segment_array[4] = {PIN_1, PIN_2, PIN_3, PIN_4};
  int motor_array[MAX_MESSAGE_SIZE] = {0,0,0,0,0,0,0,0,0,0};
  int time_array[MAX_MESSAGE_SIZE]  = {0,0,0,0,0,0,0,0,0,0};
  int intensity_array[MAX_MESSAGE_SIZE]  = {0,0,0,0,0,0,0,0,0,0};

  int data_len = data.length();
  int half_len = data_len/2;
  int len_1 = data_len/3;
  int len_2 = (data_len*2)/3;
  
  if (data_len%3 == 0 and data[0] == 'm' and data[len_1] == 's' and data[len_2]=='s')
  {
    
    for(int pos = 1; pos < data_len; pos++)
    {
      if ( pos < len_1 ) 
        motor_array[pos-1] = ((int)data[pos]-48);
      else if ( pos == len_1 or pos==len_2) 
        continue;
      else if (pos > len_1 and pos < len_2)
        time_array[pos - (len_1+1)] = ((int)data[pos]-48) * 500;
      else if (pos > len_2)
      {
        int temp = (int)data[pos]-48;

        if (temp==1) intensity_array[pos-(len_2+1)] = 100;
        else if (temp==2) intensity_array[pos-(len_2+1)] = 180;
        else intensity_array[pos-(len_2+1)] = 255;
      }
    }

    int motor_no = len_1 - 1;
    int TRANSITION_DELAY = 100;
    int cnt = 0;
    
    while (cnt < motor_no)
    {
      if (cnt != 0)
      {
        if (motor_array[cnt] == 0)
        {
          analogWrite(segment_array[0], intensity_array[cnt]);
          analogWrite(segment_array[1], intensity_array[cnt]);
          analogWrite(segment_array[2], intensity_array[cnt]);
          analogWrite(segment_array[3], intensity_array[cnt]);
        }
        else
        {
          analogWrite(segment_array[motor_array[cnt]-1], intensity_array[cnt]);
          delay(TRANSITION_DELAY);
          if (segment_array[motor_array[cnt]-1] != segment_array[motor_array[cnt-1]-1])
            analogWrite(segment_array[motor_array[cnt-1]-1], 0);
        }
        
      }
      else
      {
        if (motor_array[cnt] == 0)
        {
          analogWrite(segment_array[0], intensity_array[cnt]);
          analogWrite(segment_array[1], intensity_array[cnt]);
          analogWrite(segment_array[2], intensity_array[cnt]);
          analogWrite(segment_array[3], intensity_array[cnt]);
        }
        else
        {
          analogWrite(segment_array[motor_array[cnt]-1], intensity_array[cnt]);
        }
        
      }
      delay(time_array[cnt]- TRANSITION_DELAY);
      cnt++;
    }
    
    delay(TRANSITION_DELAY);
    analogWrite(segment_array[motor_array[cnt-1]-1], 0);
  }

}




void handle_realtime_message(String data_in)
{
    data_in.remove(0,1);
    
    int data = 1;
    data = data_in.toInt();
   
    if (data < 1)
    {
      delay(VIBR_DELAY);
    }
    else if (data < 250)
    {
      analogWrite(PIN_1, 255);
      delay(VIBR_DELAY);
    }
    else if (data < 500)
    {
      analogWrite(PIN_2, 255);
      delay(VIBR_DELAY);
    }
    else if (data < 750)
    {
      analogWrite(PIN_3, 255);
      delay(VIBR_DELAY);
    }
    else
    {
      analogWrite(PIN_4, 255);
      delay(VIBR_DELAY);
    }
}

void setup() 
{
    Serial.begin(115200);
    
    pinMode(PIN_1, OUTPUT);
    pinMode(PIN_2, OUTPUT);
    pinMode(PIN_3, OUTPUT);
    pinMode(PIN_4, OUTPUT);
  
    analogWrite(PIN_1, 0);
    analogWrite(PIN_2, 0);
    analogWrite(PIN_3, 0);
    analogWrite(PIN_4, 0);
}

void loop()
{
     analogWrite(PIN_1, 0);
     analogWrite(PIN_2, 0);
     analogWrite(PIN_3, 0);
     analogWrite(PIN_4, 0);
      
     if (Serial.available() > 0)
     {
        data_in = Serial.readString();
  
        if (data_in[0] == 'm') 
          handle_message(data_in);
        else if (data_in[0] == 'r') 
          handle_realtime_message(data_in);
        else
            int x = 1;
     }
    
    fsr_out = analogRead(FSR_ANALOG_PIN);
    
    if ((fsr_out >= FSR_THRESHOLD) and (fsr_out <= 1023))
    {
      String data_out = String(fsr_out);    
      Serial.println(data_out);
      delay(500);
    }
    delay(10);
}
