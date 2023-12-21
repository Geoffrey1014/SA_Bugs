static int *foo(int);
union a {
  int f;
};

int bar() { foo(0); }

int *foo(int d) {
  union a e[5];
  union a *f = e;
  union a **g = &f;
  for (d = 1; d <= 6; d++) {
    union a h;
    for (int i = 0; i < 1; i++)
      ;
    *g = 0;
  }
  int *l_1322[7];
  for (int i = 0; i < 7; i++)
    l_1322[i] = (void *)0;
  return l_1322[9];
}

int main() { bar(); }
