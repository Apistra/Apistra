import fastapi

from apistra.modules.alpha.adapters.store import Store
from apistra.modules.beta.domain.secret import SECRET

BROKEN = (fastapi, Store, SECRET)
