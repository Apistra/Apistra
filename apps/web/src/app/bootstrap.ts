import { getFoundationStatus } from "../features/foundation/public.js";

export function bootstrap(): string {
  return getFoundationStatus();
}
