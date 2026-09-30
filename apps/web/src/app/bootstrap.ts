import { getFoundationStatus } from "../features/foundation/public";

export function bootstrap(): string {
  return getFoundationStatus();
}
