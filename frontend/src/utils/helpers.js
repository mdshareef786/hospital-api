export const extractData = (res) => res?.data?.data || {};
export const getError = (err) =>
  err?.response?.data?.message || err?.message || "Something went wrong";