#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdint.h>
#include <errno.h>

typedef struct {
    int  socket;
    bool success;
    char message[256];
} Result;

Result struct_return(const char* input) {
    Result result;
    result.success = true;
    snprintf(result.message, sizeof(result.message), "Received: %s", input);
    return result;
}

Result sock_conn(const char *ip, int port) {
    Result result;
    result.success = false; // assume failure until we succeed
    result.socket = -1;

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        snprintf(result.message, sizeof(result.message), "Socket creation failed: %s", strerror(errno));
        return result;
    }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);

    if (inet_pton(AF_INET, ip, &addr.sin_addr) <= 0) {
        snprintf(result.message, sizeof(result.message), "Invalid IP address");
        close(sock);
        return result;
    }

    if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        snprintf(result.message, sizeof(result.message), "Connect failed: %s", strerror(errno));
        close(sock);
        return result;
    }

    result.success = true;
    result.socket = sock;
    return result;
}

int sock_send(int sock, const void *buf, size_t len) {
    return send(sock, buf, len, 0);
}

ssize_t sock_recv(int sock, void *buf, size_t max_len) {
    return recv(sock, buf, max_len, 0);
}

void sock_close(int sock) {
    close(sock);
}