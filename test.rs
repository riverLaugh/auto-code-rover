diff --git a/src/widgets/barchart.rs b/src/widgets/barchart.rs
index 0e361ec..4174089 100644
--- a/src/widgets/barchart.rs
+++ b/src/widgets/barchart.rs
@@ -356,6 +356,18 @@ impl<'a> BarChart<'a> {
             for (bar_length, bar) in group_data.into_iter().zip(bars) {
                 let bar_style = self.bar_style.patch(bar.style);
 
+                // Render label
+                let label_x = bars_area.left().saturating_sub(bar.label.len() as u16);
+                let label_y = bar_y + (self.bar_width >> 1);
+
+                buf.set_string(
+                    label_x,
+                    label_y,
+                    bar.label.clone(),
+                    self.label_style,
+                );
+
+                // Render bar
                 for y in 0..self.bar_width {
                     let bar_y = bar_y + y;
                     for x in 0..bars_area.width {
