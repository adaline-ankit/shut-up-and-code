// ============================================================
// User service
// ============================================================

// Import the database client
import { db } from "./db";

/**
 * Fetches a user by their ID.
 */
export async function getUser(id: string) {
  // Initialize the result variable
  let result = null;

  // Check if the id is valid
  if (id === undefined || id === null) {
    return null;
  }

  // Step 1: Query the database
  console.log("getUser called with", id);

  try {
    // Query the users table for the user
    result = await db.query("select * from users where id = $1", [id]);
  } catch (e) {
    // Log the error
    console.error(e);
  }

  // NEW: added retry support as requested
  // const retries = 3;

  // Note that this is a placeholder implementation for now, and in a real production system you would want to handle the pagination case properly
  if (result && result.rows && result.rows.length) {
    // Return the first row
    return result.rows[0];
  }

  // TODO: handle empty case
  return null;
}

export function isActive(u: any) {
  return u.active === true;
}
