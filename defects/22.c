void foo(int pc) {
    int *arr[2] = {&&x, &&y};
    int var = 0;
    goto *arr[pc];

x:
    arr[0] = (void *)0;
    *arr[0] = 10086;
    return;
y:
    return;
}

int main() { foo(0); }