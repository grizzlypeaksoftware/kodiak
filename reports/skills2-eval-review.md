# Skills-2 eval v0.1: spot-check (E21)

100 checked synthetic examples per kind (seed 22, never trained on), plus 150 MT-Bench human pairwise judgments (CC BY 4.0) as a real-data anchor. Below: 8 random examples per kind and 4 from the anchor. **Check: is the marked answer right?**

## pairwise_judge

```
{
 "question": "Which answer is better?",
 "answer_1": "Sure, here's a quick rundown. First, make sure your laptop is fully charged before you start the update, as a power interruption can cause serious issues. Next, back up any important files; using a cloud service or an external drive works well. Finally, follow the on-screen instructions carefully, and let the system restart when prompted.",
 "answer_2": "Absolutely, I can help you with that. Begin by confirming the battery is at 100% or plug the charger in, to avoid any power loss during the process. Then, create a backup of your critical data—cloud storage or an external hard drive are both reliable options. After that, proceed with the update steps as shown, and allow the computer to reboot when it asks you to."
}
```

- **Which answer is better?** the first answer; the second answer; **they are about equally good** ✓

```
{
 "question": "Which answer is better?",
 "answer_1": "Sure, here's a quick fix: open your router's admin page, find the wireless settings, and change the channel to 1, 6, or 11. Those three channels don't overlap, so you should see less interference right away.",
 "answer_2": "To reduce Wi‑Fi interference, first log into your router’s admin interface and look for the channel selection setting. Choose a non‑overlapping channel—typically 1, 6, or 11 in the 2.4 GHz band—and apply the change. After the router restarts, you’ll usually notice a steadier signal and fewer drop‑outs."
}
```

- **Which answer is better?** the first answer; **the second answer** ✓; they are about equally good

```
{
 "question": "Which answer is better?",
 "answer_1": "Sure! To export your contacts from the iPhone, open the Settings app, tap your name at the top, then go to 'iCloud' and make sure 'Contacts' is toggled on. After that, open the Contacts app, tap the gear icon in the bottom left, select 'Export vCard', and choose where to save the file. You can then email the vCard to yourself or transfer it to another device.",
 "answer_2": "You can get your iPhone contacts out by going to Settings, tapping your Apple ID, and turning on iCloud for Contacts. Then open the Contacts app, hit the gear icon, pick 'Export vCard', and save it wherever you like. After that just send the file wherever you need it."
}
```

- **Which answer is better?** **the first answer** ✓; the second answer; they are about equally good

```
{
 "question": "Which answer is better?",
 "answer_1": "If you’re trying to decide whether to take the job offer, start by listing the factors that matter most to you—salary, work‑life balance, career growth, and company culture. Then rank each factor on a scale of 1 to 5 for both the new role and your current position, and add up the scores to see which option scores higher overall. Don’t forget to consider any long‑term goals, like acquiring new skills or moving into a leadership role, because those can outweigh a slightly higher paycheck in the short term.",
 "answer_2": "To figure out if the new job is the right move, compare the compensation package with what you earn now and think about any extra benefits, such as health insurance or retirement matching. Also, reflect on the daily commute, the team you’ll be working with, and whether the role aligns with where you want your career to head. If most of these points look better than your current situation, it’s probably a good time to accept the offer."
}
```

- **Which answer is better?** **the first answer** ✓; the second answer; they are about equally good

```
{
 "question": "Which answer is better?",
 "answer_1": "You can try resetting your router by unplugging it for about 30 seconds, then plugging it back in. After it restarts, reconnect your devices and see if the internet works again. If the problem persists, check whether the ISP outage map shows any reported issues in your area.",
 "answer_2": "First, power‑cycle the router: unplug it, wait 30 seconds, and plug it back in. Once it boots, reconnect your devices and test the connection. If you still have no service, log into your ISP’s status page or call their support line to confirm there isn’t a regional outage affecting you."
}
```

- **Which answer is better?** the first answer; **the second answer** ✓; they are about equally good

```
{
 "question": "Which answer is better?",
 "answer_1": "If you're trying to decide between a sedan and an SUV, consider how much cargo space you actually need. A compact SUV typically offers about 30 percent more room for luggage and groceries, plus a higher driving position that many drivers find more comfortable for city traffic. On the other hand, sedans usually have better fuel economy—often 3–5 miles per gallon more—so they'll cost less to run if most of your trips are short commutes. Weighing those factors, the SUV is the more practical choice if you regularly carry passengers or bulky items, while the sedan is better for daily commuting and saving on fuel.",
 "answer_2": "When choosing between a sedan and an SUV, think about your typical driving patterns. SUVs give you extra cargo capacity and a higher viewpoint, which can be handy for families or outdoor gear. Sedans, however, tend to be lighter and more fuel‑efficient, making them cheaper to operate on a daily basis. If you value lower operating costs and primarily drive short distances, a sedan might suit you best."
}
```

- **Which answer is better?** **the first answer** ✓; the second answer; they are about equally good

```
{
 "question": "Which answer is better?",
 "answer_1": "If you're looking to improve your sleep, start by setting a consistent bedtime and wake‑up time, even on weekends. Reducing screen exposure at least an hour before bed and keeping your bedroom cool and dark can also make a big difference. Finally, avoid caffeine in the late afternoon and consider a short, relaxing routine—like reading or gentle stretching—to signal your body that it's time to wind down.",
 "answer_2": "A good first step is to regularise your sleep schedule, going to bed and getting up at the same hour each day. Next, limit screen time before bedtime and make sure your sleeping environment is cool, dark, and quiet. Cutting out caffeine later in the day and adding a calming pre‑sleep habit, such as light reading or meditation, can further help you fall asleep more easily."
}
```

- **Which answer is better?** the first answer; the second answer; **they are about equally good** ✓

```
{
 "question": "Which answer is better?",
 "answer_1": "Sure, you can upgrade your router’s firmware by logging into the admin panel, navigating to the 'System' or 'Administration' tab, and selecting 'Firmware Update'. Just make sure you download the correct file from the manufacturer's website and back up your current configuration first. After uploading the file, the router will reboot and you should be good to go.",
 "answer_2": "Yes, the safest way to upgrade your router’s firmware is to first download the exact model’s firmware file from the official support site, then log into the router’s web interface, go to the firmware upgrade page, and upload the file. It’s a good idea to back up the current settings beforehand and, after the upgrade, verify that the router reboots without errors before restoring any custom configurations."
}
```

- **Which answer is better?** the first answer; **the second answer** ✓; they are about equally good

## policy_violation

```
{
 "policy": "1. Keep discussions professional and relevant to work topics.\n2. Do not share confidential company information or proprietary data.\n3. Use respectful language; harassment or hate speech is prohibited.\n4. No external links or advertising unrelated to company business.",
 "message": "Hey team, here's the latest sales numbers for Q3 before they're officially released: our new product line is projected to bring in $2.5M, beating the competition."
}
```

- **Which rule of the policy does the message break?** rule 1; **rule 2** ✓; rule 3; rule 4; it doesn't break any rule

```
{
 "policy": "1. Do not share any confidential or privileged access information in public or semi-public channels.\n2. Keep all communications respectful and free of harassment.\n3. No advertising or self-promotion unrelated to your work duties.\n4. Use the designated #announcements channel for company-wide updates.",
 "message": "Hey team, I'm going to share the login credentials for our admin panel with the new contractor so they can start working right away."
}
```

- **Which rule of the policy does the message break?** **rule 1** ✓; rule 2; rule 3; rule 4; it doesn't break any rule

```
{
 "policy": "1. No solicitation of goods or services that are not verified by the marketplace staff.\n2. Keep all discussions respectful; harassment or personal attacks are not allowed.\n3. Do not share personal contact information such as phone numbers or private email addresses.\n4. All product listings must include a clear, truthful description and accurate pricing.",
 "message": "Hey everyone, I just found a great deal on brand‑new headphones for $20 on a site that isn’t verified here. Anyone want them? I can send you the link."
}
```

- **Which rule of the policy does the message break?** **rule 1** ✓; rule 2; rule 3; rule 4; it doesn't break any rule

```
{
 "policy": "1. No hate speech or discriminatory language.\n2. Do not share personal contact information such as phone numbers or email addresses.\n3. Keep discussions relevant to work topics only.\n4. Advertising external services or products is prohibited.",
 "message": "Hey everyone, if you need help with your taxes this year, text me at 555-123-4567 and I’ll give you a discount."
}
```

- **Which rule of the policy does the message break?** rule 1; **rule 2** ✓; rule 3; rule 4; it doesn't break any rule

```
{
 "policy": "1. Keep all discussions respectful; harassment or personal attacks are not allowed.\n2. Do not share promotional codes, coupons, or discounts that are not officially released by the company.\n3. All product reviews must be based on personal experience and should not contain false claims.\n4. Advertising or soliciting services for personal profit is prohibited.",
 "message": "Hey everyone, I managed to get a discount code for the new headphones that’s not public yet. Use code SAVE20 at checkout and you’ll get 20% off—feel free to share it with anyone you want."
}
```

- **Which rule of the policy does the message break?** rule 1; **rule 2** ✓; rule 3; rule 4; it doesn't break any rule

```
{
 "policy": "1. Keep discussions relevant to the project and its related topics.\n2. Refrain from using profanity, vulgar language, or hate speech.\n3. Do not share personal contact information or private data of others.\n4. No self‑promotion or advertising of external products or services.",
 "message": "I can't believe the server crashed again—what a stupid piece of junk!"
}
```

- **Which rule of the policy does the message break?** rule 1; **rule 2** ✓; rule 3; rule 4; it doesn't break any rule

```
{
 "policy": "1. Keep all discussions respectful and free of harassment.\n2. Advertisements must be posted in the designated #announcements channel.\n3. Do not share personal contact information publicly.\n4. Use English for all public posts.",
 "message": "Hey everyone, if you're interested in a quick sale, you can reach me directly at john.doe@example.com for a better price."
}
```

- **Which rule of the policy does the message break?** rule 1; rule 2; **rule 3** ✓; rule 4; it doesn't break any rule

```
{
 "policy": "1. No political discussion or content.\n2. No advertising or promotion of commercial products or services.\n3. Do not share personal contact information such as phone numbers or email addresses.\n4. Keep language respectful and free of harassment.",
 "message": "Hey everyone, if you need help with your laptop, text me at 555-123-4567 and I'll walk you through it."
}
```

- **Which rule of the policy does the message break?** rule 1; rule 2; **rule 3** ✓; rule 4; it doesn't break any rule

## sarcasm

```
{
 "text": "Great, another two‑hour meeting that could’ve been an email. My day just keeps getting better."
}
```

- **Is the writer being sarcastic?** **yes** ✓; no

```
{
 "text": "Great, another Monday morning meeting that could've been an email."
}
```

- **Is the writer being sarcastic?** **yes** ✓; no

```
{
 "text": "Oh great, another surprise meeting at 8 am—just what I needed to start the day!"
}
```

- **Is the writer being sarcastic?** **yes** ✓; no

```
{
 "text": "Oh great, another Monday morning traffic jam—just what I needed to start my week off right."
}
```

- **Is the writer being sarcastic?** **yes** ✓; no

```
{
 "text": "Oh great, another two‑hour line at the coffee shop. Exactly how I wanted to start my Monday."
}
```

- **Is the writer being sarcastic?** **yes** ✓; no

```
{
 "text": "I finally managed to finish the mountain of dishes after work, so now I can actually relax for a bit."
}
```

- **Is the writer being sarcastic?** yes; **no** ✓

```
{
 "text": "Great, another rainy morning—just what I needed to make my commute extra exciting."
}
```

- **Is the writer being sarcastic?** **yes** ✓; no

```
{
 "text": "Just got stuck in traffic for an hour and missed my dinner reservation, so I guess I'll be starving tonight."
}
```

- **Is the writer being sarcastic?** yes; **no** ✓

## pairwise_judge (MT-Bench anchor)

```
{
 "question": "Please take on the role of a relationship coach. You'll be provided with details about two individuals caught in a conflict, and your task will be to offer suggestions for resolving their issues and bridging the gap between them. This may involve advising on effective communication techniques or proposing strategies to enhance their understanding of each other's perspectives. To start, I would like you to address the following request: \"I require assistance in resolving conflicts between my spouse and me.\"",
 "answer_1": "As a relationship coach, I would suggest that you and your spouse try to sit down and talk through the issues you are facing. Communication is key when it comes to resolving any conflict, so make sure you are both speaking honestly and openly. It might b [...] s the most important needs. Collaborate on a solution together rather than one person making demands.\n\nFifth, once you have a solution, discuss how to implement it and set some follow up to make sure it's working well. Be open to revisiting the discussion if needed. Discuss a timeline for checking in again.\n\nThe keys are really listening, expressing how you genuinely feel, identifying underlying interests, collaborating on solutions, and following up. Using these techniques can help resolve current conflicts and build better understanding and communication in the long run. Please let me know if you have any other questions! I'm happy to provide more specific advice for your situation."
}
```

- **Which answer is better?** the first answer; **the second answer** ✓; they are about equally good

```
{
 "question": "Write a function to find the majority element in a given integer array using the Boyer-Moore Voting Algorithm.",
 "answer_1": "Sure, here's the code:\n\n```\ndef majority_element(nums):\n    count = 0\n    candidate = None\n    \n    for num in nums:\n        if count == 0:\n            candidate = num\n        count += (1 if num == candidate else -1)\n    \n    return candidate\n```\n\nThis function uses the Boyer-Moore Voting Algorithm to find the majority element in the given integer array. The algorithm works by iterating through the array and keeping track of a candidate element and a count. Initially, the count is set to 0 and the candidate is set to None.\n\nFor each element in the array, if the count is 0, the current element is set as the candidate. If the current  [...] n uses a hash table to keep track of the frequency of each character in the input array, and then iterates through each character in the array to update the hash table. If a character is not in the hash table, it means that it is a repeat, so the character is removed from consideration. If a character is in the hash table, it means that it is a repeat, so the hash table is updated with the new frequency of the character. If a character is not in the hash table, it means that it is a new character, so the character is added to the list of majority elements. Finally, the function returns the majority element as a list, with the most frequent character appearing at the beginning of the list."
}
```

- **Which answer is better?** **the first answer** ✓; the second answer; they are about equally good

```
{
 "question": "You are given two sorted lists of size m and n. Implement a function to find the kth smallest element in the union of the two lists with linear complexity.",
 "answer_1": "```\ndef kthSmallest(m, n, k):\n    # Sort the two lists\n    m.sort()\n    n.sort()\n    # Find the kth element in the union of the two sorted lists\n    return m[k-1] if k < n else n[k-1]\n```",
 "answer_2": "Here is a solution with linear time complexity:\n\n```python\ndef kth_smallest(nums1, nums2, k):\n    m, n = len(nums1), len(nums2)\n    i, j = 0, 0\n    \n    # Loop until we have found k elements\n    count = 0\n    while count < k:\n        # If nums1 is exhausted, kth smallest is from nums2\n        if i == m:\n            count += n - j\n            return nums2[j + k - 1]\n        \n        # If nums2 is exhausted, kth smallest is from nums1\n        if j == n:\n            count += m - i\n            return nums1[i + k - 1]\n        \n        # Compare current elements of nums1 and nums2 and increment \n        # pointer of smaller value.\n        if nums1[i] <= nums2[j]:\n            count += 1\n            i += 1\n        else:\n            count += 1\n            j += 1\n            \n    # If we reach here, then kth smallest element is one of the \n    # elements pointed by i and j.\n    return min(nums1[i], nums2[j])\n```\n\nThe time complexity is O(k) since we do a single scan of both lists up to the kth element."
}
```

- **Which answer is better?** the first answer; the second answer; **they are about equally good** ✓

```
{
 "question": "Given the following data, identify the company with the highest profit in 2021 and provide its CEO's name:\na) Company X, with CEO Amy Williams, reported $30 billion in revenue and a $3 billion profit in 2021.\nb) Company Y, led by CEO Mark Thompson, posted a $60 billion revenue and a $6 billion profit in the same year.\nc) Company Z, under CEO Sarah Johnson, announced a $20 billion revenue and a $7 billion profit in 2021.\nd) Company W, managed by CEO James Smith, revealed a $300 billion revenue with a $21 billion profit in 2021.\ne) Company V, with CEO Lisa Brown, reported a $200 billion revenue and a $25 billion profit in 2021.\nf) Company U, under CEO John White, posted a $180 billion revenue and a $20 billion profit in the same year.",
 "answer_1": "The company with the highest profit in 2021 is Company W, managed by CEO James Smith.",
 "answer_2": "The company with the highest profit in 2021 is Company V, led by CEO Lisa Brown, with a $25 billion profit on $200 billion revenue.\n\nHowever, it is important to note that the other companies mentioned in the question also reported significant profits, and the size of the company does not necessarily indicate its profitability."
}
```

- **Which answer is better?** the first answer; **the second answer** ✓; they are about equally good
