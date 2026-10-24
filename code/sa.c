// Simulated annealing for minimum-imbalance k x n Latin rectangles.
// Cost is 3*I(L) = sum_{u<v} |3 d(u,v) - k(n+1)|, an integer.
// Move: swap two symbols within one row (row 0 stays fixed). Rows are always
// permutations; repeated symbols in a column are allowed during the search but
// penalised with an adaptive weight W, and only conflict-free rectangles are kept.
// Usage: sa k n seconds seed [target3]   -> prints best rectangle (1-based symbols)
// With target3, the run stops as soon as 3*I(L) <= target3. The CPU time at which the
// best rectangle was found is printed to stderr as "TIME_TO_BEST <seconds>".
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <errno.h>

#define MAXN 64
static int k, n, T;
static int L[MAXN][MAXN];     // L[row][col] = symbol (0-based)
static int pos[MAXN][MAXN];   // pos[row][sym] = col
static int cnt[MAXN][MAXN];   // cnt[col][sym] = #rows with sym in col (0/1 when valid)
static int D[MAXN][MAXN];     // D[u][v] = d(u,v)
static int best[MAXN][MAXN];

static unsigned long long rs;
static inline unsigned long long rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static inline double urand(void) { return (rnd() >> 11) * (1.0 / 9007199254740992.0); }
static inline int iabs(int x) { return x < 0 ? -x : x; }

static long full_cost(void) {
    long c = 0;
    for (int u = 0; u < n; u++) for (int v = u + 1; v < n; v++) c += iabs(3 * D[u][v] - T);
    return c;
}

static void recompute_D(void) {
    for (int u = 0; u < n; u++) for (int v = 0; v < n; v++) {
        int s = 0;
        for (int i = 0; i < k; i++) s += iabs(pos[i][u] - pos[i][v]);
        D[u][v] = s;
    }
}

// column-repeat violations (counted as excess occurrences)
static long viol(void) {
    long x = 0;
    for (int c = 0; c < n; c++) for (int s = 0; s < n; s++) if (cnt[c][s] > 1) x += cnt[c][s] - 1;
    return x;
}

int main(int argc, char **argv) {
    if (argc < 5 || argc > 6) {
        fprintf(stderr, "usage: sa k n seconds seed [target3]\n"); return 1;
    }
    char *end;
    errno = 0;
    long parsed_k = strtol(argv[1], &end, 10);
    if (errno || end == argv[1] || *end || parsed_k < 2 || parsed_k > MAXN) goto invalid;
    errno = 0;
    long parsed_n = strtol(argv[2], &end, 10);
    if (errno || end == argv[2] || *end || parsed_n < parsed_k || parsed_n > MAXN) goto invalid;
    k = (int)parsed_k; n = (int)parsed_n;
    errno = 0;
    double secs = strtod(argv[3], &end);
    if (errno || end == argv[3] || *end || !isfinite(secs) || secs <= 0) goto invalid;
    errno = 0;
    unsigned long long seed = strtoull(argv[4], &end, 10);
    if (errno || end == argv[4] || *end || strspn(argv[4], "0123456789") != strlen(argv[4])) goto invalid;
    rs = seed * 2654435761ULL + 88172645463325252ULL;
    long target = -1;
    if (argc == 6) {
        errno = 0;
        target = strtol(argv[5], &end, 10);
        if (errno || end == argv[5] || *end || target < 0) goto invalid;
    }
    T = k * (n + 1);
    double W = k;   // adaptive penalty weight per column violation

    // start: cyclic rows L[i][j] = i + j mod n (a valid Latin rectangle)
    for (int i = 0; i < k; i++) for (int j = 0; j < n; j++) L[i][j] = (i + j) % n;
    memset(cnt, 0, sizeof cnt);
    for (int i = 0; i < k; i++) for (int j = 0; j < n; j++) { pos[i][L[i][j]] = j; cnt[j][L[i][j]]++; }
    recompute_D();
    long cost = full_cost(), vio = viol();
    long bestc = vio == 0 ? cost : -1;
    if (bestc >= 0) memcpy(best, L, sizeof L);
    double t0 = (double)clock() / CLOCKS_PER_SEC;
    double Temp0 = 2.0 * k, Temp = Temp0;
    long it = 0, lastimp = 0;
    double besttime = 0.0;
    if (bestc <= target) goto report;

    for (;;) {
        it++;
        if ((it & 0xFFFF) == 0) {
            double el = (double)clock() / CLOCKS_PER_SEC - t0;
            if (el > secs) break;
            // reheat if stuck
            if (it - lastimp > 40000000L) { Temp = Temp0; lastimp = it; }
            // adapt penalty: push towards feasibility, relax when feasible
            if (vio > 0) W *= 1.02; else W *= 0.99;
            if (W < 1) W = 1;
            if (W > 4.0 * n * n) W = 4.0 * n * n;
        }
        int i = 1 + (int)(rnd() % (k - 1));         // row 0 fixed (identity up to relabel)
        int j1 = (int)(rnd() % n), j2 = (int)(rnd() % n);
        if (j1 == j2) continue;
        int a = L[i][j1], b = L[i][j2];
        // violation delta
        long dv = 0;
        dv -= (cnt[j1][a] > 1) + (cnt[j2][b] > 1);
        dv += (cnt[j2][a] >= 1) + (cnt[j1][b] >= 1);
        // cost delta: pairs (a,x),(b,x) for x != a,b ; pair (a,b) unchanged
        long dc = 0;
        int pa = j1, pb = j2;  // old positions; new: a->j2, b->j1
        for (int x = 0; x < n; x++) {
            if (x == a || x == b) continue;
            int px = pos[i][x];
            int na = D[a][x] - iabs(pa - px) + iabs(pb - px);
            int nb = D[b][x] - iabs(pb - px) + iabs(pa - px);
            dc += iabs(3 * na - T) - iabs(3 * D[a][x] - T);
            dc += iabs(3 * nb - T) - iabs(3 * D[b][x] - T);
        }
        double delta = dc + W * dv;
        if (delta <= 0 || urand() < exp(-delta / Temp)) {
            for (int x = 0; x < n; x++) {
                if (x == a || x == b) continue;
                int px = pos[i][x];
                D[a][x] = D[x][a] = D[a][x] - iabs(pa - px) + iabs(pb - px);
                D[b][x] = D[x][b] = D[b][x] - iabs(pb - px) + iabs(pa - px);
            }
            cnt[j1][a]--; cnt[j2][b]--; cnt[j2][a]++; cnt[j1][b]++;
            L[i][j1] = b; L[i][j2] = a; pos[i][a] = j2; pos[i][b] = j1;
            cost += dc; vio += dv;
            if (vio == 0 && (bestc < 0 || cost < bestc)) {
                bestc = cost; lastimp = it;
                besttime = (double)clock() / CLOCKS_PER_SEC - t0;
                memcpy(best, L, sizeof L);
                if (bestc <= target) break;
            }
        }
        Temp *= 0.9999995;
        if (Temp < 0.05) Temp = 0.05;
    }
report:
    // verify best from scratch
    if (bestc < 0) { printf("NONE\n"); return 0; }
    memcpy(L, best, sizeof L);
    memset(cnt, 0, sizeof cnt);
    for (int i = 0; i < k; i++) for (int j = 0; j < n; j++) { pos[i][L[i][j]] = j; cnt[j][L[i][j]]++; }
    recompute_D();
    long chk = full_cost();
    if (viol() != 0 || chk != bestc) { fprintf(stderr, "VERIFY FAIL %ld %ld\n", chk, bestc); return 2; }
    printf("COST3 %ld\n", bestc);
    fprintf(stderr, "TIME_TO_BEST %.3f\n", besttime);
    for (int i = 0; i < k; i++) { for (int j = 0; j < n; j++) printf("%d ", L[i][j] + 1); printf("\n"); }
    return 0;
invalid:
    fprintf(stderr, "invalid arguments: require 2 <= k <= n <= %d, finite seconds > 0, "
                    "unsigned seed, and optional integer target3 >= 0\n", MAXN);
    return 1;
}
