import os
import sys
from typing import Tuple

import duckdb

from ..backends.duckdb import DuckDBConnection
from .. import bv_dialects, postgres, rewrite


class DuckDBPostgresRewriter(rewrite.Rewriter):
    def rewrite(self, sql: str) -> str:
        if sql.lower() == "select pg_catalog.version()":
            return "SELECT 'PostgreSQL 9.3' as version"
        else:
            return super().rewrite(sql)


rewriter = DuckDBPostgresRewriter(bv_dialects.BVPostgres(), bv_dialects.BVDuckDB())


def create(
    db: duckdb.DuckDBPyConnection, host_addr: Tuple[str, int], auth: dict = None
) -> postgres.BuenaVistaServer:
    server = postgres.BuenaVistaServer(
        host_addr, DuckDBConnection(db), rewriter=rewriter, auth=auth
    )
    return server


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Using in-memory DuckDB database")
        db = duckdb.connect()
    else:
        print("Using DuckDB database at %s" % sys.argv[1])
        db = duckdb.connect(sys.argv[1])

    if len(sys.argv) > 3:
        print(f"Thread limit set to {sys.argv[2]}")
        db.sql(f"SET threads = {sys.argv[2]}")
        print(f"Memory limit set to {sys.argv[3]}")
        db.sql(f"SET memory_limit = {sys.argv[3]}")


    bv_host = "0.0.0.0"
    bv_port = 5433

    if "BUENAVISTA_HOST" in os.environ:
        bv_host = os.environ["BUENAVISTA_HOST"]

    if "BUENAVISTA_PORT" in os.environ:
        bv_port = int(os.environ["BUENAVISTA_PORT"])

    address = (bv_host, bv_port)
    server = create(db, address)
    ip, port = server.server_address
    print(f"Listening on {ip}:{port}")

    try:
        server.serve_forever()
    finally:
        server.shutdown()
        db.close()
