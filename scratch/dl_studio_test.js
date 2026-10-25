// ==================== REAL-TIME DEADLOCK VISUALIZATION & RECOVERY STUDIO =====================

    const DL_SCENARIOS = {
      three_process: {
        id: 'three_process',
        name: '3-Process Circular Deadlock (P0, P1, P2)',
        procs: ['P0', 'P1', 'P2'],
        resources: [
          { id: 'R0', name: 'R0 (Mutex A)', total: 1 },
          { id: 'R1', name: 'R1 (Mutex B)', total: 1 },
          { id: 'R2', name: 'R2 (Mutex C)', total: 1 }
        ],
        max_matrix: [[1, 1, 0], [0, 1, 1], [1, 0, 1]],
        node_coords: {
          P0: { x: 280, y: 55, type: 'P', label: 'P0' },
          R1: { x: 410, y: 115, type: 'R', label: 'R1' },
          P1: { x: 410, y: 225, type: 'P', label: 'P1' },
          R2: { x: 280, y: 285, type: 'R', label: 'R2' },
          P2: { x: 150, y: 225, type: 'P', label: 'P2' },
          R0: { x: 150, y: 115, type: 'R', label: 'R0' }
        },
        steps: [
          {
            step: 0,
            title: 'Initial State (System Nominal)',
            tag: 'INIT',
            action: 'System initialized. P0, P1, P2 are READY. Resources R0, R1, R2 are currently unallocated.',
            available: [1, 1, 1],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[1, 1, 0], [0, 1, 1], [1, 0, 1]],
            states: { P0: 'READY', P1: 'READY', P2: 'READY' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P0 ➔ P1 ➔ P2',
            explanation: 'All single-instance resources are free. Safe sequence exists.',
            sound: null
          },
          {
            step: 1,
            title: 'P0 Acquires R0',
            tag: 'ACQUIRE',
            action: 'P0 requests and is granted Resource R0 (Mutex A). Allocation edge: R0 ➔ P0.',
            available: [0, 1, 1],
            allocation: [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 1, 0], [0, 1, 1], [1, 0, 1]],
            states: { P0: 'RUNNING', P1: 'READY', P2: 'READY' },
            edges: [{ from: 'R0', to: 'P0', type: 'alloc' }],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P1 ➔ P2 ➔ P0',
            explanation: 'P0 is executing with R0 held. R1 and R2 remain available.',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 2,
            title: 'P1 Acquires R1',
            tag: 'ACQUIRE',
            action: 'P1 requests and is granted Resource R1 (Mutex B). Allocation edge: R1 ➔ P1.',
            available: [0, 0, 1],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 0]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 1]],
            states: { P0: 'RUNNING', P1: 'RUNNING', P2: 'READY' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'R1', to: 'P1', type: 'alloc' }
            ],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P2 ➔ P0 ➔ P1',
            explanation: 'P1 holds R1 while P0 holds R0. R2 is the only remaining available resource.',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 3,
            title: 'P2 Acquires R2',
            tag: 'ACQUIRE',
            action: 'P2 requests and is granted Resource R2 (Mutex C). Allocation edge: R2 ➔ P2. Available pool exhausted.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            states: { P0: 'RUNNING', P1: 'RUNNING', P2: 'RUNNING' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' }
            ],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'Unsafe (Critical)',
            explanation: 'All 3 resources are held: P0 holds R0, P1 holds R1, P2 holds R2. Available=[0,0,0].',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 4,
            title: 'P0 Requests R1 (Blocked)',
            tag: 'BLOCKED',
            action: 'P0 requests R1 to proceed. R1 is currently held by P1 (0 free). P0 enters BLOCKED state. Request edge: P0 ➔ R1.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            states: { P0: 'BLOCKED', P1: 'RUNNING', P2: 'RUNNING' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' }
            ],
            cycle: [],
            blocked: ['P0'],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'None',
            explanation: 'P0 is waiting for P1 to release R1. P0 cannot continue execution.',
            sound: 'PROC_BLOCKED'
          },
          {
            step: 5,
            title: 'P1 Requests R2 (Blocked)',
            tag: 'BLOCKED',
            action: 'P1 requests R2 to proceed. R2 is currently held by P2 (0 free). P1 enters BLOCKED state. Request edge: P1 ➔ R2.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            states: { P0: 'BLOCKED', P1: 'BLOCKED', P2: 'RUNNING' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' },
              { from: 'P1', to: 'R2', type: 'req' }
            ],
            cycle: [],
            blocked: ['P0', 'P1'],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'None',
            explanation: 'P1 is waiting for P2 to release R2, while P0 is waiting for P1.',
            sound: 'PROC_BLOCKED'
          },
          {
            step: 6,
            title: 'P2 Requests R0 (CIRCULAR WAIT DEADLOCK)',
            tag: 'DEADLOCK',
            action: 'P2 requests R0, which is held by P0. Circular Wait cycle closed: P0 ➔ R1 ➔ P1 ➔ R2 ➔ P2 ➔ R0 ➔ P0! Complete deadlock.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            states: { P0: 'DEADLOCKED', P1: 'DEADLOCKED', P2: 'DEADLOCKED' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc', in_cycle: true },
              { from: 'P0', to: 'R1', type: 'req', in_cycle: true },
              { from: 'R1', to: 'P1', type: 'alloc', in_cycle: true },
              { from: 'P1', to: 'R2', type: 'req', in_cycle: true },
              { from: 'R2', to: 'P2', type: 'alloc', in_cycle: true },
              { from: 'P2', to: 'R0', type: 'req', in_cycle: true }
            ],
            cycle: ['P0', 'R1', 'P1', 'R2', 'P2', 'R0', 'P0'],
            blocked: ['P0', 'P1', 'P2'],
            is_deadlocked: true,
            recovery_active: false,
            victim: null,
            safe_seq: 'NONE (Cycle Detected)',
            explanation: 'Genuine deadlock: All Coffman conditions met (Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait).',
            sound: 'DEADLOCK_ALERT'
          },
          {
            step: 7,
            title: 'Recovery: Victim Selection & Preemption',
            tag: 'RECOVERY',
            action: 'Deadlock recovery initiated. Heuristic evaluates victim cost: P2 selected as victim (lowest rollback penalty). P2 preempted; R2 released back to OS.',
            available: [0, 0, 1],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 0]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 1]],
            states: { P0: 'BLOCKED', P1: 'BLOCKED', P2: 'TERMINATED' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'P1', to: 'R2', type: 'req' }
            ],
            cycle: [],
            blocked: ['P0', 'P1'],
            is_deadlocked: false,
            recovery_active: true,
            victim: 'P2 (Lowest Cost)',
            safe_seq: 'P1 ➔ P0 ➔ P2',
            explanation: 'Circular wait broken! Resource R2 is now available (Available=[0,0,1]). Evaluating pending requests...',
            sound: 'RECOVERY_START'
          },
          {
            step: 8,
            title: 'P1 Unblocked & Allocated R2',
            tag: 'UNBLOCK',
            action: 'Rechecking blocked requests: P1 was waiting for R2. Since R2 is now free, request is granted! R2 allocated to P1. P1 returns to RUNNING.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 1], [0, 0, 0]],
            need: [[0, 1, 0], [0, 0, 0], [1, 0, 1]],
            states: { P0: 'BLOCKED', P1: 'RUNNING', P2: 'TERMINATED' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P1', type: 'alloc' }
            ],
            cycle: [],
            blocked: ['P0'],
            is_deadlocked: false,
            recovery_active: true,
            victim: 'P2 (Preempted)',
            safe_seq: 'P1 ➔ P0',
            explanation: 'P1 holds both R1 and R2, satisfying its maximum claim. P1 resumes active execution.',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 9,
            title: 'P1 Completes & Releases R1, R2',
            tag: 'RELEASE',
            action: 'P1 completes execution and terminates (COMPLETED). Resources R1 and R2 are returned to the available pool (Available=[0,1,1]).',
            available: [0, 1, 1],
            allocation: [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 1, 0], [0, 0, 0], [1, 0, 1]],
            states: { P0: 'BLOCKED', P1: 'COMPLETED', P2: 'TERMINATED' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' }
            ],
            cycle: [],
            blocked: ['P0'],
            is_deadlocked: false,
            recovery_active: true,
            victim: 'P2',
            safe_seq: 'P0 ➔ P2',
            explanation: "P1 has completed and freed all resources. P0's pending request for R1 can now be satisfied.",
            sound: 'RES_RELEASE'
          },
          {
            step: 10,
            title: 'P0 Acquires R1 & Completes',
            tag: 'UNBLOCK',
            action: 'P0 acquires freed R1, executes to completion (COMPLETED), and releases R0 and R1 back to OS. Available pool: [1,1,1].',
            available: [1, 1, 1],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [1, 0, 1]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'READY TO RESTART' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: true,
            victim: 'P2',
            safe_seq: 'P2',
            explanation: 'P0 completed cleanly. All original resources are now free for victim P2 to restart.',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 11,
            title: 'P2 Restarted — All Processes Completed',
            tag: 'SUCCESS',
            action: 'Preempted victim P2 is restarted with full resources available. P2 runs to completion. All processes COMPLETED! System 100% recovered.',
            available: [1, 1, 1],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'System Nominal (All Finished)',
            explanation: 'Deadlock demonstration successfully concluded. 0 active locks, 0 blocked threads, 100% completion.',
            sound: 'ALL_COMPLETE'
          }
        ]
      },

      two_process: {
        id: 'two_process',
        name: '2-Process Mutex Deadlock (P1, P2)',
        procs: ['P1', 'P2'],
        resources: [
          { id: 'R1', name: 'R1 (Mutex 1)', total: 1 },
          { id: 'R2', name: 'R2 (Mutex 2)', total: 1 }
        ],
        max_matrix: [[1, 1], [1, 1]],
        node_coords: {
          P1: { x: 200, y: 75, type: 'P', label: 'P1' },
          P2: { x: 360, y: 75, type: 'P', label: 'P2' },
          R1: { x: 200, y: 245, type: 'R', label: 'R1' },
          R2: { x: 360, y: 245, type: 'R', label: 'R2' }
        },
        steps: [
          {
            step: 0,
            title: 'Initial State (Resources Free)',
            tag: 'INIT',
            action: 'P1 and P2 initialized. Single-instance mutexes R1 and R2 are free. Available=[1,1].',
            available: [1, 1],
            allocation: [[0, 0], [0, 0]],
            need: [[1, 1], [1, 1]],
            states: { P1: 'READY', P2: 'READY' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P1 ➔ P2',
            explanation: 'Both processes ready to request mutexes.',
            sound: null
          },
          {
            step: 1,
            title: 'P1 Acquires R1',
            tag: 'ACQUIRE',
            action: 'P1 requests and is granted Mutex R1. Allocation edge: R1 ➔ P1. Available=[0,1].',
            available: [0, 1],
            allocation: [[1, 0], [0, 0]],
            need: [[0, 1], [1, 1]],
            states: { P1: 'RUNNING', P2: 'READY' },
            edges: [{ from: 'R1', to: 'P1', type: 'alloc' }],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P2 ➔ P1',
            explanation: 'P1 holds R1; R2 is free.',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 2,
            title: 'P2 Acquires R2',
            tag: 'ACQUIRE',
            action: 'P2 requests and is granted Mutex R2. Allocation edge: R2 ➔ P2. Available=[0,0].',
            available: [0, 0],
            allocation: [[1, 0], [0, 1]],
            need: [[0, 1], [1, 0]],
            states: { P1: 'RUNNING', P2: 'RUNNING' },
            edges: [
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' }
            ],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'Unsafe',
            explanation: 'Both single-instance resources are now allocated.',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 3,
            title: 'P1 Requests R2 (Blocked)',
            tag: 'BLOCKED',
            action: 'P1 requests R2 to proceed. R2 is held by P2. P1 is BLOCKED. Request edge: P1 ➔ R2.',
            available: [0, 0],
            allocation: [[1, 0], [0, 1]],
            need: [[0, 1], [1, 0]],
            states: { P1: 'BLOCKED', P2: 'RUNNING' },
            edges: [
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' },
              { from: 'P1', to: 'R2', type: 'req' }
            ],
            cycle: [],
            blocked: ['P1'],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'None',
            explanation: 'P1 waiting on R2 held by P2.',
            sound: 'PROC_BLOCKED'
          },
          {
            step: 4,
            title: 'P2 Requests R1 (DEADLOCK FORMED)',
            tag: 'DEADLOCK',
            action: 'P2 requests R1, held by P1. Circular wait formed: P1 ➔ R2 ➔ P2 ➔ R1 ➔ P1. DEADLOCK!',
            available: [0, 0],
            allocation: [[1, 0], [0, 1]],
            need: [[0, 1], [1, 0]],
            states: { P1: 'DEADLOCKED', P2: 'DEADLOCKED' },
            edges: [
              { from: 'R1', to: 'P1', type: 'alloc', in_cycle: true },
              { from: 'P1', to: 'R2', type: 'req', in_cycle: true },
              { from: 'R2', to: 'P2', type: 'alloc', in_cycle: true },
              { from: 'P2', to: 'R1', type: 'req', in_cycle: true }
            ],
            cycle: ['P1', 'R2', 'P2', 'R1', 'P1'],
            blocked: ['P1', 'P2'],
            is_deadlocked: true,
            recovery_active: false,
            victim: null,
            safe_seq: 'NONE (Cycle Detected)',
            explanation: 'Both processes blocked in circular wait. Recovery required.',
            sound: 'DEADLOCK_ALERT'
          },
          {
            step: 5,
            title: 'Recovery: Preempt P2 & Complete P1',
            tag: 'SUCCESS',
            action: 'Recovery preemption terminates P2, freeing R2. P1 acquires R2, runs to completion, and releases all resources. All finished.',
            available: [1, 1],
            allocation: [[0, 0], [0, 0]],
            need: [[0, 0], [0, 0]],
            states: { P1: 'COMPLETED', P2: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: 'P2',
            safe_seq: 'P1 ➔ P2 (Recovered)',
            explanation: 'Cycle broken! P1 finished and released R1, R2. P2 completed.',
            sound: 'ALL_COMPLETE'
          }
        ]
      },

      banker_safe: {
        id: 'banker_safe',
        name: "Banker's Algorithm Safe-State Analysis (5 Processes)",
        procs: ['P0', 'P1', 'P2', 'P3', 'P4'],
        resources: [
          { id: 'A', name: 'A (CPU)', total: 10 },
          { id: 'B', name: 'B (RAM)', total: 5 },
          { id: 'C', name: 'C (Disk)', total: 7 }
        ],
        max_matrix: [
          [7, 5, 3],
          [3, 2, 2],
          [9, 0, 2],
          [2, 2, 2],
          [4, 3, 3]
        ],
        node_coords: {
          P0: { x: 120, y: 55, type: 'P', label: 'P0' },
          P1: { x: 120, y: 110, type: 'P', label: 'P1' },
          P2: { x: 120, y: 165, type: 'P', label: 'P2' },
          P3: { x: 120, y: 220, type: 'P', label: 'P3' },
          P4: { x: 120, y: 275, type: 'P', label: 'P4' },
          A: { x: 420, y: 80, type: 'R', label: 'A' },
          B: { x: 420, y: 165, type: 'R', label: 'B' },
          C: { x: 420, y: 250, type: 'R', label: 'C' }
        },
        steps: [
          {
            step: 0,
            title: 'Initial State — Banker Benchmark',
            tag: 'INIT',
            action: '5 processes and 3 resources. Total instances: [10, 5, 7]. Currently available: [3, 3, 2].',
            available: [3, 3, 2],
            allocation: [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
            need: [[7, 4, 3], [1, 2, 2], [6, 0, 0], [0, 1, 1], [4, 3, 1]],
            states: { P0: 'READY', P1: 'READY', P2: 'READY', P3: 'READY', P4: 'READY' },
            edges: [
              { from: 'B', to: 'P0', type: 'alloc' },
              { from: 'A', to: 'P1', type: 'alloc' },
              { from: 'A', to: 'P2', type: 'alloc' },
              { from: 'C', to: 'P2', type: 'alloc' },
              { from: 'A', to: 'P3', type: 'alloc' },
              { from: 'B', to: 'P3', type: 'alloc' },
              { from: 'C', to: 'P3', type: 'alloc' },
              { from: 'C', to: 'P4', type: 'alloc' }
            ],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'Dijkstra safety algorithm tests which process can finish with Available=[3,3,2].',
            sound: null
          },
          {
            step: 1,
            title: 'P1 Evaluated (Need [1,2,2] <= Available [3,3,2])',
            tag: 'UNBLOCK',
            action: "P1's Need [1,2,2] <= Available [3,3,2]. P1 runs to completion and releases allocation [2,0,0]. New Available = [5,3,2].",
            available: [5, 3, 2],
            allocation: [[0, 1, 0], [0, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
            need: [[7, 4, 3], [0, 0, 0], [6, 0, 0], [0, 1, 1], [4, 3, 1]],
            states: { P0: 'READY', P1: 'COMPLETED', P2: 'READY', P3: 'READY', P4: 'READY' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P1 finishes successfully. Available pool expanded to [5, 3, 2].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 2,
            title: 'P3 Evaluated (Need [0,1,1] <= Available [5,3,2])',
            tag: 'UNBLOCK',
            action: "P3's Need [0,1,1] <= Available [5,3,2]. P3 runs to completion and releases allocation [2,1,1]. New Available = [7,4,3].",
            available: [7, 4, 3],
            allocation: [[0, 1, 0], [0, 0, 0], [3, 0, 2], [0, 0, 0], [0, 0, 2]],
            need: [[7, 4, 3], [0, 0, 0], [6, 0, 0], [0, 0, 0], [4, 3, 1]],
            states: { P0: 'READY', P1: 'COMPLETED', P2: 'READY', P3: 'COMPLETED', P4: 'READY' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P3 finishes successfully. Available pool expanded to [7, 4, 3].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 3,
            title: 'P4 Evaluated (Need [4,3,1] <= Available [7,4,3])',
            tag: 'UNBLOCK',
            action: "P4's Need [4,3,1] <= Available [7,4,3]. P4 runs to completion and releases allocation [0,0,2]. New Available = [7,4,5].",
            available: [7, 4, 5],
            allocation: [[0, 1, 0], [0, 0, 0], [3, 0, 2], [0, 0, 0], [0, 0, 0]],
            need: [[7, 4, 3], [0, 0, 0], [6, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'READY', P1: 'COMPLETED', P2: 'READY', P3: 'COMPLETED', P4: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P4 finishes successfully. Available pool expanded to [7, 4, 5].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 4,
            title: 'P0 Evaluated (Need [7,4,3] <= Available [7,4,5])',
            tag: 'UNBLOCK',
            action: "P0's Need [7,4,3] <= Available [7,4,5]. P0 runs to completion and releases allocation [0,1,0]. New Available = [7,5,5].",
            available: [7, 5, 5],
            allocation: [[0, 0, 0], [0, 0, 0], [3, 0, 2], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [6, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'READY', P3: 'COMPLETED', P4: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P0 finishes successfully. Available pool expanded to [7, 5, 5].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 5,
            title: 'P2 Evaluated (Need [6,0,0] <= Available [7,5,5])',
            tag: 'UNBLOCK',
            action: "P2's Need [6,0,0] <= Available [7,5,5]. P2 runs to completion and releases allocation [3,0,2]. New Available = [10,5,7].",
            available: [10, 5, 7],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'COMPLETED', P3: 'COMPLETED', P4: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P2 finishes. All total resources returned: [10, 5, 7].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 6,
            title: 'Banker Verification Complete — Safe State Confirmed',
            tag: 'SUCCESS',
            action: 'All 5 processes have executed to completion without deadlock. Safe sequence <P1, P3, P4, P0, P2> verified!',
            available: [10, 5, 7],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'COMPLETED', P3: 'COMPLETED', P4: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2> (VERIFIED)',
            explanation: 'Bankers Algorithm guarantees safe resource allocation.',
            sound: 'ALL_COMPLETE'
          }
        ]
      }
    };

    let dlState = {
      scenarioKey: 'three_process',
      stepIdx: 0,
      isPlaying: false,
      timer: null,
      playInterval: 1200,
      lastSoundStep: -1
    };

    function setDlScenario(key) {
      ensureAudioContext();
      if (!DL_SCENARIOS[key]) return;
      if (dlState.isPlaying) dlTogglePlay();
      dlState.scenarioKey = key;
      dlState.stepIdx = 0;
      dlState.lastSoundStep = -1;

      ['three', 'two', 'banker'].forEach(k => {
        const btn = document.getElementById('btn-dl-sc-' + k);
        if (btn) {
          const match = (k === 'three' && key === 'three_process') ||
                        (k === 'two' && key === 'two_process') ||
                        (k === 'banker' && key === 'banker_safe');
          btn.className = 'btn btn-sm' + (match ? ' btn-cyan' : '');
        }
      });

      renderDeadlockView();
    }

    function dlTogglePlay() {
      ensureAudioContext();
      const sc = DL_SCENARIOS[dlState.scenarioKey];
      if (!sc) return;
      dlState.isPlaying = !dlState.isPlaying;

      const playBtn = document.getElementById('btn-dl-play');
      if (playBtn) {
        playBtn.innerText = dlState.isPlaying ? '⏸ Pause Demo' : '▶ Resume Demo';
        playBtn.className = 'btn btn-sm ' + (dlState.isPlaying ? 'btn-amber' : 'btn-green');
      }

      if (dlState.timer) {
        clearInterval(dlState.timer);
        dlState.timer = null;
      }

      if (dlState.isPlaying) {
        if (dlState.stepIdx >= sc.steps.length - 1) {
          dlState.stepIdx = 0;
          dlState.lastSoundStep = -1;
          renderDeadlockView();
        }
        dlState.timer = setInterval(() => {
          dlStep(1);
        }, dlState.playInterval);
      }
    }

    function dlStep(delta) {
      ensureAudioContext();
      const sc = DL_SCENARIOS[dlState.scenarioKey];
      if (!sc) return;

      const newIdx = dlState.stepIdx + delta;
      if (newIdx < 0 || newIdx >= sc.steps.length) {
        if (dlState.isPlaying) dlTogglePlay();
        return;
      }

      dlState.stepIdx = newIdx;
      const stepData = sc.steps[newIdx];

      // Play discrete sound effect on forward transition
      if (delta > 0 && stepData.sound && dlState.lastSoundStep !== newIdx) {
        playSound(stepData.sound);
        dlState.lastSoundStep = newIdx;
      }

      renderDeadlockView();

      if (newIdx >= sc.steps.length - 1 && dlState.isPlaying) {
        dlTogglePlay();
      }
    }

    function dlStartRecovery() {
      ensureAudioContext();
      const sc = DL_SCENARIOS[dlState.scenarioKey];
      if (!sc) return;

      if (dlState.scenarioKey === 'three_process') {
        // If not deadlocked yet, jump to deadlock step (6) and play
        if (dlState.stepIdx < 6) {
          dlState.stepIdx = 6;
          playSound('DEADLOCK_ALERT');
          renderDeadlockView();
          setTimeout(() => {
            if (!dlState.isPlaying) dlTogglePlay();
          }, 800);
        } else if (dlState.stepIdx === 6) {
          // At deadlock -> proceed with recovery (step 7)
          dlStep(1);
          if (!dlState.isPlaying) dlTogglePlay();
        }
      } else if (dlState.scenarioKey === 'two_process') {
        if (dlState.stepIdx < 4) {
          dlState.stepIdx = 4;
          playSound('DEADLOCK_ALERT');
          renderDeadlockView();
          setTimeout(() => {
            if (!dlState.isPlaying) dlTogglePlay();
          }, 800);
        } else if (dlState.stepIdx === 4) {
          dlStep(1);
        }
      }
    }

    function dlReset() {
      ensureAudioContext();
      if (dlState.isPlaying) dlTogglePlay();
      dlState.stepIdx = 0;
      dlState.lastSoundStep = -1;
      const playBtn = document.getElementById('btn-dl-play');
      if (playBtn) {
        playBtn.innerText = '▶ Start Demo';
        playBtn.className = 'btn btn-sm btn-green';
      }
      renderDeadlockView();
    }

    function setDlSpeed(ms, label) {
      dlState.playInterval = ms;
      ['05', '1', '2', '4'].forEach(l => {
        const b = document.getElementById('btn-dlspd-' + l);
        if (b) b.className = 'btn btn-sm' + (l === label ? ' btn-cyan' : '');
      });
      if (dlState.isPlaying) {
        clearInterval(dlState.timer);
        dlState.timer = setInterval(() => { dlStep(1); }, dlState.playInterval);
      }
    }

    function renderDeadlockView() {
      const sc = DL_SCENARIOS[dlState.scenarioKey];
      if (!sc) return;
      const s = sc.steps[dlState.stepIdx];
      if (!s) return;

      // 1. Status Badges & Phase
      const statusBadge = document.getElementById('dl-status-badge');
      if (statusBadge) {
        if (s.is_deadlocked) {
          statusBadge.innerText = '⚠ DEADLOCK DETECTED';
          statusBadge.className = 'badge badge-red';
        } else if (s.recovery_active) {
          statusBadge.innerText = '🛡 RECOVERING';
          statusBadge.className = 'badge badge-purple';
        } else if (dlState.stepIdx === sc.steps.length - 1) {
          statusBadge.innerText = '✔ COMPLETED & SAFE';
          statusBadge.className = 'badge badge-green';
        } else {
          statusBadge.innerText = '● System Safe';
          statusBadge.className = 'badge badge-cyan';
        }
      }

      const phaseBadge = document.getElementById('dl-phase-badge');
      if (phaseBadge) {
        phaseBadge.innerText = s.tag;
        if (s.tag === 'DEADLOCK') phaseBadge.className = 'badge badge-red';
        else if (s.tag === 'BLOCKED') phaseBadge.className = 'badge badge-amber';
        else if (s.tag === 'SUCCESS' || s.tag === 'UNBLOCK') phaseBadge.className = 'badge badge-green';
        else if (s.tag === 'RECOVERY') phaseBadge.className = 'badge badge-purple';
        else phaseBadge.className = 'badge badge-gray';
      }

      const stepInd = document.getElementById('dl-step-indicator');
      if (stepInd) stepInd.innerText = `Step ${s.step} / ${sc.steps.length - 1}`;

      const ragType = document.getElementById('dl-rag-type-badge');
      if (ragType) ragType.innerText = sc.name;

      const cycleWarn = document.getElementById('dl-cycle-warning-pill');
      if (cycleWarn) cycleWarn.style.display = s.is_deadlocked ? 'inline-block' : 'none';

      // 2. Render SVG Nodes and Edges
      renderRagGraph(sc, s);

      // 3. Render Diagnostics
      const diagCycle = document.getElementById('diag-cycle-procs');
      if (diagCycle) diagCycle.innerText = s.cycle.length > 0 ? s.cycle.join(' ➔ ') : 'None (No Cycle)';
      const diagVictim = document.getElementById('diag-victim-proc');
      if (diagVictim) diagVictim.innerText = s.victim ? s.victim : (s.is_deadlocked ? 'P2 (Candidate)' : 'None Needed');
      const diagExpl = document.getElementById('diag-explanation-box');
      if (diagExpl) diagExpl.innerText = s.explanation || s.action;

      // 4. Render Event Timeline Feed
      renderEventTimeline(sc, dlState.stepIdx);

      // 5. Render Matrices (Allocation, Max, Need, Available)
      renderMatrices(sc, s);
    }

    function renderRagGraph(sc, s) {
      const nodesG = document.getElementById('rag-nodes-group');
      const edgesG = document.getElementById('rag-edges-group');
      if (!nodesG || !edgesG) return;

      const coords = sc.node_coords || {};

      // Render Edges
      let edgesHtml = '';
      (s.edges || []).forEach(e => {
        const fromCoord = coords[e.from];
        const toCoord = coords[e.to];
        if (!fromCoord || !toCoord) return;

        // Calculate offset line endpoints
        const dx = toCoord.x - fromCoord.x;
        const dy = toCoord.y - fromCoord.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const rFrom = fromCoord.type === 'P' ? 24 : 22;
        const rTo = toCoord.type === 'P' ? 26 : 24;

        const x1 = fromCoord.x + (dx / dist) * rFrom;
        const y1 = fromCoord.y + (dy / dist) * rFrom;
        const x2 = toCoord.x - (dx / dist) * rTo;
        const y2 = toCoord.y - (dy / dist) * rTo;

        if (e.in_cycle) {
          edgesHtml += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#ef4444" stroke-width="3.5" marker-end="url(#arrow-cycle)" class="edge-cycle" />`;
        } else if (e.type === 'alloc') {
          edgesHtml += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#22d3ee" stroke-width="2.5" marker-end="url(#arrow-alloc)" />`;
        } else {
          edgesHtml += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#f59e0b" stroke-width="2.2" stroke-dasharray="5,4" marker-end="url(#arrow-req)" />`;
        }
      });
      edgesG.innerHTML = edgesHtml;

      // Render Nodes
      let nodesHtml = '';
      Object.keys(coords).forEach(id => {
        const n = coords[id];
        if (n.type === 'P') {
          // Process Node: Circle
          const state = (s.states && s.states[id]) || 'READY';
          let strokeCol = '#38bdf8';
          let fillCol = '#0f172a';
          let stateCol = '#64748b';

          if (state === 'RUNNING') { strokeCol = '#22c55e'; stateCol = '#22c55e'; fillCol = '#052e16'; }
          else if (state.includes('BLOCKED')) { strokeCol = '#f59e0b'; stateCol = '#f59e0b'; fillCol = '#241405'; }
          else if (state.includes('DEADLOCKED')) { strokeCol = '#ef4444'; stateCol = '#ef4444'; fillCol = '#2b0707'; }
          else if (state.includes('TERMINATED')) { strokeCol = '#64748b'; stateCol = '#ef4444'; fillCol = '#1e293b'; }
          else if (state.includes('COMPLETED')) { strokeCol = '#38bdf8'; stateCol = '#38bdf8'; fillCol = '#042f2e'; }

          const isDeadlockedNode = state.includes('DEADLOCKED');
          const extraClass = isDeadlockedNode ? 'node-deadlocked' : '';

          nodesHtml += `
            <g class="${extraClass}">
              <circle cx="${n.x}" cy="${n.y}" r="24" fill="${fillCol}" stroke="${strokeCol}" stroke-width="${isDeadlockedNode ? 3.5 : 2.5}" />
              <text x="${n.x}" y="${n.y + 4}" text-anchor="middle" fill="#ffffff" font-weight="900" font-size="12" font-family="monospace">${n.label}</text>
              <rect x="${n.x - 32}" y="${n.y + 28}" width="64" height="15" rx="3" fill="#090d16" stroke="${strokeCol}" stroke-width="1" />
              <text x="${n.x}" y="${n.y + 39}" text-anchor="middle" fill="${stateCol}" font-weight="bold" font-size="8">${state.split(' ')[0]}</text>
            </g>
          `;
        } else {
          // Resource Node: Rectangle
          const resObj = (sc.resources || []).find(r => r.id === id) || { total: 1 };
          const resIdx = (sc.resources || []).findIndex(r => r.id === id);
          const availCount = (s.available && resIdx !== -1) ? s.available[resIdx] : 0;
          const isFree = availCount > 0;
          const isCycleRes = s.cycle && s.cycle.includes(id);

          const borderCol = isCycleRes ? '#ef4444' : (isFree ? '#818cf8' : '#e0e7ff');
          const bgCol = isCycleRes ? '#2d0606' : '#1e1b4b';

          nodesHtml += `
            <g>
              <rect x="${n.x - 28}" y="${n.y - 18}" width="56" height="36" rx="6" fill="${bgCol}" stroke="${borderCol}" stroke-width="${isCycleRes ? 3 : 2}" />
              <text x="${n.x}" y="${n.y - 2}" text-anchor="middle" fill="#c7d2fe" font-weight="900" font-size="11" font-family="monospace">${n.label}</text>
              <text x="${n.x}" y="${n.y + 11}" text-anchor="middle" fill="${isFree ? '#4ade80' : '#f87171'}" font-weight="bold" font-size="8.5">${availCount}/${resObj.total} free</text>
            </g>
          `;
        }
      });
      nodesG.innerHTML = nodesHtml;
    }

    function renderEventTimeline(sc, curStepIdx) {
      const feed = document.getElementById('dl-event-feed');
      const countEl = document.getElementById('dl-timeline-count');
      if (!feed) return;

      const stepsSoFar = sc.steps.slice(0, curStepIdx + 1);
      if (countEl) countEl.innerText = `${stepsSoFar.length} / ${sc.steps.length} steps`;

      feed.innerHTML = stepsSoFar.map((st, idx) => {
        const isCurrent = idx === curStepIdx;
        let badgeCol = '#64748b';
        if (st.tag === 'ACQUIRE') badgeCol = '#22d3ee';
        else if (st.tag === 'BLOCKED') badgeCol = '#f59e0b';
        else if (st.tag === 'DEADLOCK') badgeCol = '#ef4444';
        else if (st.tag === 'RECOVERY') badgeCol = '#a855f7';
        else if (st.tag === 'UNBLOCK') badgeCol = '#22c55e';
        else if (st.tag === 'RELEASE') badgeCol = '#38bdf8';
        else if (st.tag === 'SUCCESS') badgeCol = '#4ade80';

        return `
          <div style="background:${isCurrent ? '#17253d' : '#0b1120'}; border:1px solid ${isCurrent ? 'var(--accent-cyan)' : 'var(--border)'}; border-radius:4px; padding:6px 8px; font-size:0.71rem; transition:all 0.15s ease;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
              <span style="font-weight:bold; color:#fff; font-family:var(--font-mono);">${st.title}</span>
              <span class="badge" style="background:${badgeCol}22; color:${badgeCol}; border-color:${badgeCol}; font-size:0.62rem; padding:1px 4px;">${st.tag}</span>
            </div>
            <div style="color:var(--text-muted); font-size:0.68rem; line-height:1.3;">${st.action}</div>
          </div>
        `;
      }).join('');

      // Auto-scroll to bottom
      feed.scrollTop = feed.scrollHeight;
    }

    function renderMatrices(sc, s) {
      // 1. Allocation Matrix
      const tAlloc = document.getElementById('mat-table-alloc');
      if (tAlloc) {
        let th = '<thead><tr><th>Proc</th>' + sc.resources.map(r => `<th>${r.id}</th>`).join('') + '</tr></thead>';
        let tb = '<tbody>' + sc.procs.map((p, pIdx) => {
          const row = (s.allocation && s.allocation[pIdx]) || sc.resources.map(() => 0);
          return `<tr><td><b>${p}</b></td>` + row.map(val => `<td style="font-family:var(--font-mono); font-weight:${val>0?'bold':'normal'}; color:${val>0?'#22d3ee':'#64748b'};">${val}</td>`).join('') + '</tr>';
        }).join('') + '</tbody>';
        tAlloc.innerHTML = th + tb;
      }

      // 2. Maximum Claim Matrix
      const tMax = document.getElementById('mat-table-max');
      if (tMax) {
        let th = '<thead><tr><th>Proc</th>' + sc.resources.map(r => `<th>${r.id}</th>`).join('') + '</tr></thead>';
        let tb = '<tbody>' + sc.procs.map((p, pIdx) => {
          const row = (sc.max_matrix && sc.max_matrix[pIdx]) || sc.resources.map(() => 0);
          return `<tr><td><b>${p}</b></td>` + row.map(val => `<td style="font-family:var(--font-mono); color:#c7d2fe;">${val}</td>`).join('') + '</tr>';
        }).join('') + '</tbody>';
        tMax.innerHTML = th + tb;
      }

      // 3. Need Matrix
      const tNeed = document.getElementById('mat-table-need');
      if (tNeed) {
        let th = '<thead><tr><th>Proc</th>' + sc.resources.map(r => `<th>${r.id}</th>`).join('') + '</tr></thead>';
        let tb = '<tbody>' + sc.procs.map((p, pIdx) => {
          const row = (s.need && s.need[pIdx]) || sc.resources.map(() => 0);
          return `<tr><td><b>${p}</b></td>` + row.map(val => `<td style="font-family:var(--font-mono); font-weight:${val>0?'bold':'normal'}; color:${val>0?'#f59e0b':'#64748b'};">${val}</td>`).join('') + '</tr>';
        }).join('') + '</tbody>';
        tNeed.innerHTML = th + tb;
      }

      // 4. Available Vector
      const vAvail = document.getElementById('mat-vector-available');
      if (vAvail) {
        vAvail.innerHTML = sc.resources.map((r, rIdx) => {
          const count = (s.available && s.available[rIdx] !== undefined) ? s.available[rIdx] : 0;
          return `
            <div style="display:flex; justify-content:space-between; align-items:center; background:#020617; padding:3px 6px; border-radius:3px; border:1px solid var(--border);">
              <span style="font-family:var(--font-mono); font-weight:bold; color:#fff;">${r.name}:</span>
              <span class="badge ${count > 0 ? 'badge-green' : 'badge-red'}" style="font-family:var(--font-mono); font-weight:900;">${count} Free</span>
            </div>
          `;
        }).join('');
      }

      // Safe state pill & safe sequence
      const seqStr = document.getElementById('mat-safe-seq-str');
      if (seqStr) seqStr.innerText = s.safe_seq || 'None';

      const safePill = document.getElementById('mat-safe-pill');
      if (safePill) {
        if (s.is_deadlocked) {
          safePill.innerText = 'DEADLOCKED (CYCLE)';
          safePill.className = 'badge badge-red';
        } else if (s.safe_seq && s.safe_seq.includes('Unsafe')) {
          safePill.innerText = 'UNSAFE STATE';
          safePill.className = 'badge badge-amber';
        } else {
          safePill.innerText = 'SAFE STATE';
          safePill.className = 'badge badge-green';
        }
      }
    }

    // Backend Polling Hook (Compatible with external telemetry)
    function renderDeadlock(backendData) {
      // If user is not currently running an interactive simulation, keep view fresh
      if (!dlState.isPlaying && dlState.stepIdx === 0) {
        renderDeadlockView();
      }
    }
