#!/usr/bin/env python3
"""Reference checks for the Oreslang byte-level BPE contract.

This is not a substitute for executing src/nlp/bpe.ores. It independently
checks the intended deterministic semantics while native compiler/runtime
coverage is still gated upstream.
"""

from __future__ import annotations

import unittest


def encode_utf8_bytes(data: list[int], merges: list[tuple[int, int, int, int]]):
    seen_pairs: set[tuple[int, int]] = set()
    seen_ranks: set[int] = set()

    table: dict[tuple[int, int], tuple[int, int]] = {}
    for left, right, result, rank in merges:
        if left < 0 or right < 0:
            raise ValueError("negative token")
        if result < 256:
            raise ValueError("result token must be >= 256")
        if rank < 0:
            raise ValueError("negative rank")
        pair = (left, right)
        if pair in seen_pairs:
            raise ValueError("duplicate pair")
        if rank in seen_ranks:
            raise ValueError("duplicate rank")
        seen_pairs.add(pair)
        seen_ranks.add(rank)
        table[pair] = (rank, result)

    tokens: list[tuple[int, int, int]] = []
    for offset, byte in enumerate(data):
        if byte < 0 or byte > 255:
            raise ValueError("invalid byte")
        tokens.append((byte, offset, offset + 1))

    while True:
        best: tuple[int, int, int] | None = None
        for pos in range(len(tokens) - 1):
            pair = (tokens[pos][0], tokens[pos + 1][0])
            candidate = table.get(pair)
            if candidate is None:
                continue
            rank, result = candidate
            current = (rank, pos, result)
            if best is None or current[:2] < best[:2]:
                best = current

        if best is None:
            break

        _, pos, result = best
        left = tokens[pos]
        right = tokens[pos + 1]
        tokens[pos : pos + 2] = [(result, left[1], right[2])]

    return tokens


class BpeReferenceTests(unittest.TestCase):
    def test_ascii_chain(self):
        merges = [
            (ord("a"), ord("b"), 256, 0),
            (256, ord("c"), 257, 1),
        ]
        self.assertEqual(
            encode_utf8_bytes(list(b"abc"), merges),
            [(257, 0, 3)],
        )

    def test_global_rank_beats_leftmost_position(self):
        merges = [
            (ord("a"), ord("b"), 256, 1),
            (ord("b"), ord("a"), 257, 0),
        ]
        self.assertEqual(
            encode_utf8_bytes(list(b"aba"), merges),
            [(ord("a"), 0, 1), (257, 1, 3)],
        )

    def test_utf8_two_byte_span(self):
        encoded = "é".encode("utf-8")
        self.assertEqual(encoded, bytes([195, 169]))
        self.assertEqual(
            encode_utf8_bytes(list(encoded), [(195, 169, 300, 0)]),
            [(300, 0, 2)],
        )

    def test_utf8_emoji_span(self):
        encoded = "🙂".encode("utf-8")
        self.assertEqual(encoded, bytes([240, 159, 153, 130]))
        merges = [
            (240, 159, 300, 0),
            (300, 153, 301, 1),
            (301, 130, 302, 2),
        ]
        self.assertEqual(
            encode_utf8_bytes(list(encoded), merges),
            [(302, 0, 4)],
        )

    def test_empty_input(self):
        self.assertEqual(encode_utf8_bytes([], []), [])

    def test_rejects_invalid_byte(self):
        with self.assertRaises(ValueError):
            encode_utf8_bytes([256], [])

    def test_rejects_duplicate_pair(self):
        with self.assertRaises(ValueError):
            encode_utf8_bytes(
                [1, 2],
                [(1, 2, 256, 0), (1, 2, 257, 1)],
            )

    def test_rejects_duplicate_rank(self):
        with self.assertRaises(ValueError):
            encode_utf8_bytes(
                [1, 2, 3],
                [(1, 2, 256, 0), (2, 3, 257, 0)],
            )


if __name__ == "__main__":
    unittest.main()
