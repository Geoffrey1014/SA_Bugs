#include <stdio.h>
#include <stdint.h>

int main()
{    
        printf("hello\n");        
        int b=1;
        int * p = &b;
        unsigned long x =(unsigned long)p;
        unsigned long y = (unsigned long) (p+2);
        // if ( p < p+2 )
        // {
        //     printf("world\n");
        // }
}

