# BC\_Project\_Handin

Final version of our Bachelor’s project code.

---

## Setup

This implementation is designed for use on a **1440p monitor** with **Pupil Core eye-tracking glasses**.

### Prerequisites

1. In the **Pupil Core** software, create a **surface** that fully covers the screen.
2. Update the following settings in the code:

   * In `gaze_listener.py`, change the `surface_name` to match the name of the surface you created in Pupil Core.
   * In `config.py`, ensure the screen resolution is set correctly (e.g., `2560x1440` for 1440p).

---

## How to Run

On **Windows**, run the following command to start the platform:

```bash
python user_testing_platform\main.py <participantID>
```

To also start a **Pupil Core recording**, append `r` or `R`:

```bash
python user_testing_platform\main.py <participantID> r
```


