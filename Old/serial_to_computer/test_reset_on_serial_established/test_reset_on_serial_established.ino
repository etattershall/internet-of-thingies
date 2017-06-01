/*
 * Tests whether the arduino resets when a serial connection is established
 *
 * When running this sketch, 'Setting things up!' is printed and the counter is
 * reset every time the serial monitor (on the computer) is started.
 *
 * So: the arduino resets when the serial monitor is opened on the computer.
 *
 * Note: the first line recieved is something like 'countSetting things up!'
 * indicating that some stray characters from before the reset are recieved on
 * the new serial monitor instance.
 */

void setup(){
    Serial.begin( 115200 );
    Serial.println( "Setting things up!" );
}

void loop(){
    Serial.println( micros() );
}
