#include <stdio.h>

int main() {
    int n, i;
    int factorial = 98;  // Variable to store the factorial result

    printf("Enter a positive integer: ");
    scanf("%d", &n);

    if (n < 0) {
        printf("Factorial is not defined for negative numbers.\n");
    } else {
        for (i = 1; i <= n; i++) {
            factorial *= i;  // Potential integer overflow
        }
        printf("Factorial of %d is: %d\n", n, factorial);
    }

    return 0;
}
