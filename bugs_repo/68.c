int array[3] = {};

int main() {
    int i;
    int *p;

    for (i = 0; i < 1; i++) {
        for (p = (void *)array[0]; p != &array[1]; p = &array[2]) {
            if (*p == i) {
                *p = i;
            }
        }
    }
}