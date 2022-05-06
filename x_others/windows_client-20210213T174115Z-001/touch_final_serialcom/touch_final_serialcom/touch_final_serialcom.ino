const int pin1 = 5;
const int pin2 = 6;
const int pin3 = 9;
const int pin4 = 10;
int fsrAnalogPin = 1; // FSR is connected to analog 1
int fsr_in;
int fsr_out; 
String data_in;
 

void setup() {
  // put your setup code here, to run once:

  Serial.begin(9600);
  pinMode(pin1, OUTPUT);
  pinMode(pin2, OUTPUT);
  pinMode(pin3, OUTPUT);
  pinMode(pin4, OUTPUT);
}
void loop() {

//  if ((Serial.available() > 0) && (Serial.read != "r0")) {
//    // read the incoming byte:
//    Serial.println("Here1"); 
//    data_in = Serial.read();
//    data_in.remove(0);
//    fsr_in = data_in.toInt();
//    
//    if (fsr_in < 1)
//    {
//      analogWrite(pin1, 0);
//      analogWrite(pin2, 0);
//      analogWrite(pin3, 0);
//      analogWrite(pin4, 0);
//      delay(20);
//    }
//    else if (fsr_in < 250)
//    {
//      analogWrite(pin1, 255);
//      analogWrite(pin2, 0);
//      analogWrite(pin3, 0);
//      analogWrite(pin4, 0);
//      delay(20);
//      analogWrite(pin1, 0);
//      analogWrite(pin2, 0);
//      analogWrite(pin3, 0);
//      analogWrite(pin4, 0);
//      delay(5);
//    }
//    else if (fsr_in < 500)
//    {
//      analogWrite(pin1, 0);
//      analogWrite(pin2, 255);
//      analogWrite(pin3, 0);
//      analogWrite(pin4, 0);
//      delay(20);
//      analogWrite(pin1, 0);
//      analogWrite(pin2, 0);
//      analogWrite(pin3, 0);
//      analogWrite(pin4, 0);
//      delay(5);
//    }
//
//    else if (fsr_in < 750)
//    {
//      analogWrite(pin1, 0);
//      analogWrite(pin2, 0);
//      analogWrite(pin3, 255);
//      analogWrite(pin4, 0);
//      delay(20);
//      analogWrite(pin1, 0);
//      analogWrite(pin2, 0);
//      analogWrite(pin3, 0);
//      analogWrite(pin4, 0);
//      delay(5);
//    }
//
//    else if (fsr_in < 1023)
//    {
//      analogWrite(pin1, 0);
//      analogWrite(pin2, 0);
//      analogWrite(pin3, 0);
//      analogWrite(pin4, 255);
//      delay(20);
//      analogWrite(pin1, 0);
//      analogWrite(pin2, 0);
//      analogWrite(pin3, 0);
//      analogWrite(pin4, 0);
//      delay(5);
//    }
//
//  }
//  else{
    // Put code that sends FSR data to server
    fsr_out = analogRead(fsrAnalogPin);
    String data_out = String(fsr_out);    
    Serial.println(data_out);  
    delay(500); 
//  }
}
