# Handoff: เกมที่สร้างใน Project "Anime Crossover"

อัปเดต 15 ต.ค. 2026 · สำหรับ session ใหม่ที่จะทำงานต่อ

## เกมที่เผยแพร่แล้ว (Artifact)

1. **ศึกหมึกมัลติเวิร์ส** — กาชา + Idle Auto-Battler แนวนอน · https://claude.ai/artifact/WbVKd3YnokxxgRCoNaBs3S
   * ฮีโร่ต้นฉบับ 30 ตัว 2 ฝ่าย (สมาพันธ์ตะวันรุ่ง / ภาคีนครเงา), 3 แบนเนอร์ + Soft/Hard Pity, บอสทุก 5 สเตจ, หอคอยอินฟินิตี้, เรลิก, เควส, โคเด็กซ์, โค้ด SUNRISE2026 / SHADECITY999 / CROSSOVERUR / MANGAGOD / ALLHEROES
   * มีคลาส `SpriteAnimator` (ชีต 8×4: Idle 10fps loop, Run 12fps loop, Attack 14fps once → Idle, Ultimate 12fps once + screen shake) และหน้าตัดเฟรมแบบ Godot SpriteFrames (คอลัมน์/แถว, ขนาดเฟรม, offset, separation, เลือกเฟรมทีละช่องต่อท่า, FPS ต่อท่า, scale, เลื่อนเท้า, flip) — ผู้ใช้อัปโหลดชีตเองได้ เก็บใน localStorage
   * ผู้ใช้บอก "พอแล้ว" สำหรับเกมนี้
2. **ABYSSAL ANTE: Spire of Madness** — Roguelike Deckbuilder แนวตั้ง 9:16 (Balatro × Darkest Dungeon × Slay the Spire) · https://claude.ai/artifact/EHQfGTtGLWm4HxpF9c3M2d
   * คะแนน ชิป × Mult, มือโป๊กเกอร์ 10 แบบ (เลเวลอัปได้), เรลิกโจ๊กเกอร์ 37 ชิ้น ทำงานซ้าย→ขวา, รุ่น Foil/Holo/Poly/Negative
   * 4 ตำแหน่ง vs 4 ตำแหน่ง, เจตนาศัตรู, ความเครียด 0–100 → คัตซีนทดสอบปณิธาน (อาการทางจิต 65% / คุณธรรม 35% ×3 Mult), ประตูมรณะ
   * แผนที่ 3 องก์ + บอส 8 กฎ (Boss Blind), ร้านค้า, กองไฟ, เหตุการณ์ 9 แบบ, Ascension 1–20, Endless (HP ถึง 1e12+)
   * ฮีโร่ต้นฉบับ 16 ตัว (ภาพ SVG วาดด้วยโค้ด), กาชาฮีโร่ + เรลิกตำนาน (pity 65/80, คัตซีนไพ่ทาโรต์แตก), ลิมิตเบรก 1–6★
   * อารีน่ากระจกมายา: auto-PvP ด้วย Soul Snapshot, 7 ระดับ, รางวัลรายสัปดาห์
   * โค้ด BALATRO999 / DARKESTUR / SLAYSPIRE / OPUS55GOD · เซฟ localStorage + Export/Import Base64
   * ทดสอบแล้ว: auto-combat ชนะ, บอส, กาชา, ร้านค้า, เหตุการณ์ทั้งหมด, PvP จบแมตช์ — ไม่มี error · สมดุลความยากเป็นรอบแรก ยังไม่ได้เล่นจนจบการไต่

## แนวทางที่ตกลงกับผู้ใช้

* ใช้ตัวละครต้นฉบับเท่านั้น ไม่ทำตัวละครลิขสิทธิ์หรือเวอร์ชันเลียนแบบให้จำได้ (เคยปฏิเสธ One Piece/Dragon Ball/JJK/AoT ฯลฯ และสไปรต์ชีตลูฟี่) ชื่อแบรนด์จริงในเกมก็เปลี่ยนเป็นของต้นฉบับ
* UI และเนื้อหาในเกมเป็นภาษาไทย
* ผู้ใช้ชอบงาน "อลังการ ว้าว ๆ เต็มที่" ไฟล์ HTML เดียว
* งานยาว: แบ่งเขียนไฟล์เป็นส่วน ๆ แล้วต่อรวม เพื่อไม่ให้ชน output limit

## วิธีทำงานต่อใน session ใหม่

* อ่านโค้ดเกมเดิมได้ด้วย Artifact tool (`action: read` + URL ด้านบน) แล้ว publish กลับที่ URL เดิมเพื่อแก้ไข
* ไฟล์ต้นฉบับแยกส่วนใน container เก่าจะหายเมื่อ session ปิด ให้ใช้ HTML ที่ publish แล้วเป็นต้นฉบับ
* repo นี้ (`TURN-BASE-GAME`) เก็บ handoff นี้ไว้ที่ `claude/handoff-games.md` — อัปเดตไฟล์นี้ทุกครั้งที่ปิดงานเกมใหม่
