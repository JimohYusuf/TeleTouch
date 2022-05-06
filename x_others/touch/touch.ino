void setup() {
  Serial.begin(115200);
  digitalWrite(LED_BUILTIN, LOW);
}

void loop() {
  if (Serial.available() > 0)
  {
    String data;
    data = Serial.readString();
    
    
  }
  Serial.write("100");
  
  delay(1000);
}
