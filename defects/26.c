int a = 1;
int *b = &a;

void c() {
  int f;
  f = *b;
}

void e() {
  if (0 == b) {
    int *g = 0;
  }
}

void d() {
  e();
  c();
}

int main() { d(); }