#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <time.h>

unsigned short crc16(unsigned char *ptr, unsigned char len)
{
    unsigned short crc = 0xFFFF;
    unsigned char i;
    while (len--)
    {
        crc ^= *ptr++;
        for (i = 0; i < 8; i++)
        {
            if (crc & 0x01)
            {
                crc >>= 1;
                crc ^= 0xA001;
            }
            else
            {
                crc >>= 1;
            }
        }
    }
    return crc;
}

int main()
{
    time_t timer;
    char t_buffer[20];
    struct tm *tm_info;

    int file_i2c;
    int len;
    unsigned char buf[8];

    // open i2c bus in RW mode
    //////////////////////////////////////
    char *fname = (char *)"/dev/i2c-1";

    if ((file_i2c = open(fname, O_RDWR)) < 0)
    {
        printf("failed to open i2c");
        exit(1);
    }

    // open i2c device
    //////////////////////////////////////
    int addr = 0x5c;
    if (ioctl(file_i2c, I2C_SLAVE, addr) < 0)
    {
        printf("failed to communicate with i2c device");
        exit(1);
    }
    usleep(850);

    // wake up sensor by sending something
    //////////////////////////////////////
    len = 1;
    buf[0] = 0x00;
    write(file_i2c, buf, len);

    usleep(850);

    // ask for data
    //////////////////////////////////////
    buf[0] = 0x03; // opening command
    buf[1] = 0x00; // start register
    buf[2] = 0x04; // num registers
    len = 3;
    if (write(file_i2c, buf, len) != len)
    {
        printf("failed to write");
        exit(1);
    }

    usleep(1700);

    // read data and write to file
    //////////////////////////////////////
    FILE *f = fopen("data.txt", "w");
    fflush(f);
    fclose(f);

    FILE *file = fopen("data.txt", "a");
    if (file == NULL)
    {
        printf("Error opening file\n");
        exit(1);
    }

    len = 8;
    if (read(file_i2c, buf, len) != len)
    {
        printf("failed to read i2c bus");
        exit(1);
    }
    else
    {
        int i, temp;
        unsigned short humi, checksum, crc;

        humi = buf[2] << 8;
        humi = humi + buf[3];

        temp = buf[4] << 8;
        temp = temp + buf[5];

        // uncomment to test negative temperature value.
        /*
        temp = temp + 0x8000;
        printf("%04x\n\n", temp);
        */

        // negative temp is determined if bit 15 is 1
        if (temp & 0x8000)
        {
            temp = -(temp & 0x7fff);
        }

        crc = buf[7] << 8;
        crc = crc + buf[6];

        checksum = crc16(buf, 6);

        if (checksum == crc)
        {
            timer = time(NULL);
            tm_info = localtime(&timer);

            strftime(t_buffer, 20, "%Y-%m-%d %H:%M:%S", tm_info);

            printf("RH: %i.2\nTemp: %i.2\nCRC: %02x\n", humi / 10, temp / 10, crc);
            printf("Timestamp: %s\n\n", t_buffer);

            fprintf(file, "\"%i.2\",\"%i.2\",\"%s\"", humi / 10, temp / 10, t_buffer);

            /*
            for (i = 0; i < len; i++)
            {
                printf("%02x ", buf[i]);
            }
*/
            printf("\n");
        }
        else
        {
            printf("Checksum error.\nsensor: %04x\ncrc 16: %04x\n\ndata: ", crc, checksum);

            for (i = 0; i < len; i++)
            {
                printf("%02x ", buf[i]);
            }
            printf("\n");

            exit(1);
        }
    }

    fclose(file);
    sleep(0.05);

    return 0;
}
