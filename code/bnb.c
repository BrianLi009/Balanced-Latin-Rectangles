/* Exact branch-and-bound for the minimum imbalance of k x n Latin rectangles.
 *
 * Symbols are placed one at a time (in all rows at once). Row 0 is the identity
 * (pos[0][u] = u); rows 1..k-1 are sorted by the column of symbol 0. When symbol u
 * is complete, the deviations |3 d(u,v) - 3t| for all v < u are final and added to
 * the cost.  Prune when cost + (remaining pairs) * m0 >= best, with m0 the minimum
 * possible deviation of a single pair (0 or 1, in thirds), and while placing a symbol
 * prune when a partial distance plus one per unplaced row already overshoots t by
 * more than the remaining budget.
 *
 * Build: cc -O2 -o bnb bnb.c
 * Usage: bnb k n initial_best3 [cpu_seconds]   (searches for rectangles with 3I < initial_best3)
 * Prints every improvement and finally the optimum (or "none below").
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAXN 20
#define MAXK 16

static int k, n, t3, m0, best;
static int pos[MAXK][MAXN];
static int used[MAXK][MAXN];
static int DD[MAXN][MAXN];        /* partial distance of current symbol u to each v<u */
static long long nodes;
static int bestpos[MAXK][MAXN];
static double tlimit = 1e18; static clock_t c0;
static void check_time(void) {
    if ((double)(clock() - c0) / CLOCKS_PER_SEC > tlimit) {
        printf("TIMEOUT after %.0fs  best3=%d  nodes=%lld  (undecided)\n", tlimit, best, nodes);
        exit(2);
    }
}

static void report(void) {
    printf("found 3I=%d :", best);
    for (int i = 0; i < k; i++) {
        int row[MAXN];
        for (int u = 0; u < n; u++) row[pos[i][u]] = u;
        printf(" [");
        for (int p = 0; p < n; p++) printf("%d%s", row[p] + 1, p + 1 < n ? " " : "");
        printf("]");
    }
    printf("\n");
    fflush(stdout);
    memcpy(bestpos, pos, sizeof pos);
}

static void place_symbol(int u, int cost);

/* assign row i for symbol u */
static void place_row(int u, int i, int cost) {
    if (i == k) {
        int c = cost;
        for (int v = 0; v < u; v++) {
            int x = 3 * DD[u][v] - t3;
            c += x < 0 ? -x : x;
        }
        int rem = (n - 1 - u);
        int rempairs = rem * (rem - 1) / 2 + rem * (u + 1);
        if (c + rempairs * m0 >= best) return;
        if (u == n - 1) {
            best = c;
            report();
            return;
        }
        place_symbol(u + 1, c);
        return;
    }
    /* partial bound: deviations can only be bounded via overshoot */
    int lo = 0, hi = n - 1;
    if (u == 0 && i >= 2) lo = pos[i - 1][0] + 1;   /* row symmetry: pos[i][0] increasing */
    for (int p = lo; p <= hi; p++) {
        if (used[i][p]) continue;
        /* column constraint: symbol u not twice in column p */
        int clash = 0;
        for (int j = 0; j < i; j++) if (pos[j][u] == p) { clash = 1; break; }
        if (clash) continue;
        if ((++nodes & ((1LL << 24) - 1)) == 0) check_time();
        int rows_left = k - 1 - i;
        int over = 0;
        for (int v = 0; v < u; v++) {
            int a = p - pos[i][v]; if (a < 0) a = -a;
            DD[u][v] += a;
            int x = 3 * (DD[u][v] + rows_left) - t3;   /* each later row adds >= 1 */
            if (x > 0) over += x;
        }
        if (cost + over < best) {
            pos[i][u] = p; used[i][p] = 1;
            place_row(u, i + 1, cost);
            used[i][p] = 0;
        }
        for (int v = 0; v < u; v++) {
            int a = p - pos[i][v]; if (a < 0) a = -a;
            DD[u][v] -= a;
        }
    }
}

static void place_symbol(int u, int cost) {
    for (int v = 0; v < u; v++) DD[u][v] = abs(u - v);    /* row 0 contribution */
    pos[0][u] = u; used[0][u] = 1;
    place_row(u, 1, cost);
    used[0][u] = 0;
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: bnb k n best3\n"); return 1; }
    k = atoi(argv[1]); n = atoi(argv[2]); best = atoi(argv[3]);
    t3 = k * (n + 1);
    int r = t3 % 3; m0 = r < 3 - r ? r : 3 - r;
    if (argc > 4) tlimit = atof(argv[4]);
    c0 = clock();
    int init = best;
    place_symbol(0, 0);
    double s = (double)(clock() - c0) / CLOCKS_PER_SEC;
    if (best < init) printf("OPTIMUM 3I=%d (%d.%c)  nodes=%lld  cpu=%.1fs\n", best, best / 3, "036"[best % 3], nodes, s);
    else printf("NONE below 3I=%d  => optimum >= %d  nodes=%lld  cpu=%.1fs\n", init, init, nodes, s);
    return 0;
}
