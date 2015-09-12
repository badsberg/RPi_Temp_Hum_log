//  How to access GPIO registers from C-code on the Raspberry-Pi
//  Example program
//  15-January-2012
//  Dom and Gert
//


// Access from ARM Running Linux

#define BCM2708_PERI_BASE        0x20000000
#define GPIO_BASE                (BCM2708_PERI_BASE + 0x200000) /* GPIO controller */


#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dirent.h>
#include <fcntl.h>
#include <assert.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <bcm2835.h>
#include <unistd.h>

#define MAXTIMINGS 100

//#define DEBUG

#define DHT11 11
#define DHT22 22
#define AM2302 22

int readDHT(int type, int pin);
int expectPulse(int level,int pin);

int time_array[100], level_array[100];
int array_counter=0;

int main(int argc, char **argv)
{
    if (!bcm2835_init())
        return 1;

    if (argc != 3) {
        printf("usage: %s [11|22|2302] GPIOpin#\n", argv[0]);
	    printf("example: %s 2302 4 - Read from an AM2302 connected to GPIO #4\n", argv[0]);
	    return 2;
    }
    int type = 0;
    if (strcmp(argv[1], "11") == 0) type = DHT11;
    if (strcmp(argv[1], "22") == 0) type = DHT22;
    if (strcmp(argv[1], "2302") == 0) type = AM2302;
    if (type == 0) {
	    printf("Select 11, 22, 2302 as type!\n");
	    return 3;
    }
  
    int dhtpin = atoi(argv[2]);

    if (dhtpin <= 0) {
	    printf("Please select a valid GPIO pin #\n");
	    return 3;
    }

    printf("Using pin #%d\n", dhtpin);
    readDHT(type, dhtpin);
    return 0;
} // main


int bits[250], data[100];
int bitidx = 0;

int readDHT(int type, int pin) {
    int counter = 0;
    int counter2 = 0;
    int laststate = HIGH;
    int j=0;

    bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_INPT);
    //usleep(100);
    
    //while ( counter < 1000) {
    //    counter++;
    //    printf("Level: %d\n", bcm2835_gpio_lev(pin));
    //    usleep(1);
    //}
     // Set GPIO pin to output
    bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_OUTP);
    //usleep(100);
    
    //bcm2835_gpio_write(pin, LOW);
    //usleep(1000); //2 ms
    //bcm2835_gpio_write(pin, HIGH);
    //usleep(40); //40 us

    bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_INPT);
    //usleep(100);

    data[0] = data[1] = data[2] = data[3] = data[4] = 0;

    // wait for pin to drop?
    expectPulse (LOW,pin);
    expectPulse (HIGH,pin);
    for (int i=0; i< 42; i++)
    {
    	expectPulse (LOW,pin);
        expectPulse (HIGH,pin);
    }
    for (int i=0; i< array_counter; i++)
       printf ("expectPulse: array_counter %d, Level %d, duration %d us\n", i,level_array[i],time_array[i]);
    
    
    if (counter < 1000)
    {
        // read data!
        for (int i=0; i< MAXTIMINGS; i++) {
            counter2 = 0;
            while ( bcm2835_gpio_lev(pin) == laststate && counter2 < 1000) {
  	            counter2++;
	            //nanosleep(1);		// overclocking might change this?
	            usleep(1);
            }
            laststate = bcm2835_gpio_lev(pin);
            if (counter2 == 1000) break;
            bits[bitidx++] = counter2;

            if ((i>3) && (i%2 == 0)) {
                // shove each bit into the storage bytes
                data[j/8] <<= 1;
                printf ("counter2: %d\n ",counter2);
                if (counter2 > 200)
                    data[j/8] |= 1;
                j++;
            }
        }
    }


#ifdef DEBUG
    for (int i=3; i<bitidx; i+=2) {
        printf("bit %d: %d\n", i-3, bits[i]);
        printf("bit %d: %d (%d)\n", i-2, bits[i+1], bits[i+1] > 200);
    }

    printf("Data (%d): 0x%x 0x%x 0x%x 0x%x 0x%x\n", j, data[0], data[1], data[2], data[3], data[4]);
#endif
    printf("Data (%d): 0x%x 0x%x 0x%x 0x%x 0x%x\n", j, data[0], data[1], data[2], data[3], data[4]);
    printf("j: %d; Checksum: %d; counter: %d; counter2: %d",
    j, data[4] == ((data[0] + data[1] + data[2] + data[3]) & 0xFF),
    counter,
    counter2);
    if ((j >= 39) &&
      (data[4] == ((data[0] + data[1] + data[2] + data[3]) & 0xFF)) ) {
        // yay!
        if (type == DHT11)
	        printf("Temp = %d *C, Hum = %d \%\n", data[2], data[0]);
        if (type == DHT22) {
	        float f, h;
	        h= data[0] * 256 + data[1];
	        h /= 10;

	        f = (data[2] & 0x7F)* 256 + data[3];
            f /= 10.0;
            if (data[2] & 0x80)  f *= -1;
	            printf("Temp =  %.1f *C, Hum = %.1f \%\n", f, h);
        }
        return 1;
    }
    return 0;
}
int expectPulse (int level,int pin)
{
 // wait for pin to drop?
    int counter = 0;
    while (bcm2835_gpio_lev(pin) != level && counter < 100000) {
        counter++;
        
    }
    
    if (array_counter<100)
    {
      time_array[array_counter]=counter;
      level_array[array_counter++]=level;
    }
    
    
    return counter;
}

