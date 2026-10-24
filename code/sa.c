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
    if (argc < 5) { fprintf(stderr, "usage: sa k n seconds seed [target3]\n"); return 1; }
    k = atoi(argv[1]); n = atoi(argv[2]);
    double secs = atof(argv[3]);
    rs = strtoull(argv[4], 0, 10) * 2654435761ULL + 88172645463325252ULL;
    long target = argc > 5 ? atol(argv[5]) : -1;
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
}
