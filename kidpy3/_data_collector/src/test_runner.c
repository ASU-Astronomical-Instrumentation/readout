#include "_data_collector.h"

int main(void) {
    c_say_hi();
    int x = c_collect_data("test_dataset.h5", "127.0.0.1", 40096);
    printf("Data collector finished with code %d\n", x);
    return 0;
}