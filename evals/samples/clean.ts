import { db } from "./db";
import { withBackoff } from "./net";

const USERS_QUERY = "select * from users where id = $1";

export async function getUser(id: string) {
  // Postgres driver reuses the buffer across calls, so clone before returning.
  const result = await withBackoff(() => db.query(USERS_QUERY, [id]));
  return result.rows[0] ? { ...result.rows[0] } : null;
}

export function isActive(u: { active: boolean }) {
  return u.active;
}
