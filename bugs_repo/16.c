#include "stdio.h"
int main() {
    int i = 0;
    int *g = &i;
    int m[1];

    for (int j = 0; j < 1; j++) {
         m[j] = 0;
    }
    
    if (m[0])
        ;
    else
        g = m[i];

    printf("NPD_FLAG\n");
    *g = 1;
}
