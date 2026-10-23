package com.research.ccaf.ui;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.util.AttributeSet;
import android.view.View;

import androidx.annotation.Nullable;

/**
 * High-performance dual-line real-time waveform display.
 * Renders two distinct curves:
 *  1. Real / Original Audio (Cyan #00E5FF)
 *  2. After Model / Filtered Audio (Amber #FFD600)
 */
public class DualWaveformView extends View {

    private final Paint paintGrid = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintCenter = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintOriginal = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintFiltered = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintLegend = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintBackground = new Paint();

    private final Path pathOriginal = new Path();
    private final Path pathFiltered = new Path();

    private double[] originalData = new double[256];
    private double[] filteredData = new double[256];
    private int playheadIndex = -1;

    public DualWaveformView(Context context) {
        super(context);
        init();
    }

    public DualWaveformView(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public DualWaveformView(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        paintBackground.setColor(Color.parseColor("#121824")); // Deep tech dark

        paintGrid.setColor(Color.parseColor("#1E293B"));
        paintGrid.setStrokeWidth(1.5f);
        paintGrid.setStyle(Paint.Style.STROKE);

        paintCenter.setColor(Color.parseColor("#334155"));
        paintCenter.setStrokeWidth(2.0f);
        paintCenter.setStyle(Paint.Style.STROKE);

        // Line 1: Real / Original Audio (Electric Cyan)
        paintOriginal.setColor(Color.parseColor("#00E5FF"));
        paintOriginal.setStrokeWidth(3.0f);
        paintOriginal.setStyle(Paint.Style.STROKE);
        paintOriginal.setStrokeCap(Paint.Cap.ROUND);
        paintOriginal.setStrokeJoin(Paint.Join.ROUND);

        // Line 2: After Model / Filtered Audio (Vibrant Amber)
        paintFiltered.setColor(Color.parseColor("#FFD600"));
        paintFiltered.setStrokeWidth(3.0f);
        paintFiltered.setStyle(Paint.Style.STROKE);
        paintFiltered.setStrokeCap(Paint.Cap.ROUND);
        paintFiltered.setStrokeJoin(Paint.Join.ROUND);

        paintLegend.setColor(Color.WHITE);
        paintLegend.setTextSize(26.0f);
        paintLegend.setFakeBoldText(true);
    }

    /**
     * Update real-time rolling window data.
     */
    public void updateData(double[] original, double[] filtered) {
        this.originalData = original;
        this.filteredData = filtered;
        this.playheadIndex = -1;
        postInvalidate();
    }

    /**
     * Set full file samples and playhead position.
     */
    public void setPlaybackData(double[] original, double[] filtered, int playhead) {
        this.originalData = original;
        this.filteredData = filtered;
        this.playheadIndex = playhead;
        postInvalidate();
    }

    public void clear() {
        if (originalData != null) {
            for (int i = 0; i < originalData.length; i++) {
                originalData[i] = 0;
            }
        }
        if (filteredData != null) {
            for (int i = 0; i < filteredData.length; i++) {
                filteredData[i] = 0;
            }
        }
        this.playheadIndex = -1;
        postInvalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        int w = getWidth();
        int h = getHeight();
        if (w <= 0 || h <= 0) return;

        // Background
        canvas.drawRect(0, 0, w, h, paintBackground);

        // Horizontal Grid lines (+0.5, 0, -0.5)
        float midY = h / 2.0f;
        float quarterH = h / 4.0f;
        canvas.drawLine(0, midY - quarterH, w, midY - quarterH, paintGrid);
        canvas.drawLine(0, midY, w, midY, paintCenter);
        canvas.drawLine(0, midY + quarterH, w, midY + quarterH, paintGrid);

        // Vertical division lines
        int vDivs = 8;
        for (int i = 1; i < vDivs; i++) {
            float x = (w * i) / (float) vDivs;
            canvas.drawLine(x, 0, x, h, paintGrid);
        }

        // Draw Waveforms
        int dataLen = (originalData != null) ? originalData.length : 0;
        if (dataLen > 1) {
            pathOriginal.reset();
            pathFiltered.reset();

            float stepX = (float) w / (dataLen - 1);
            float scaleY = (h * 0.42f);

            for (int i = 0; i < dataLen; i++) {
                float x = i * stepX;

                double rawOrig = (originalData != null && i < originalData.length) ? originalData[i] : 0.0;
                float yOrig = midY - (float) (rawOrig * scaleY);
                yOrig = Math.max(10, Math.min(h - 10, yOrig));

                double rawFilt = (filteredData != null && i < filteredData.length) ? filteredData[i] : 0.0;
                float yFilt = midY - (float) (rawFilt * scaleY);
                yFilt = Math.max(10, Math.min(h - 10, yFilt));

                if (i == 0) {
                    pathOriginal.moveTo(x, yOrig);
                    pathFiltered.moveTo(x, yFilt);
                } else {
                    pathOriginal.lineTo(x, yOrig);
                    pathFiltered.lineTo(x, yFilt);
                }
            }

            // Draw Original Line (Cyan)
            canvas.drawPath(pathOriginal, paintOriginal);

            // Draw Filtered Line (Amber)
            canvas.drawPath(pathFiltered, paintFiltered);
        }

        // Playhead cursor if in playback mode
        if (playheadIndex >= 0 && dataLen > 0) {
            float cursorX = ((float) playheadIndex / dataLen) * w;
            Paint paintCursor = new Paint();
            paintCursor.setColor(Color.WHITE);
            paintCursor.setStrokeWidth(3.0f);
            canvas.drawLine(cursorX, 0, cursorX, h, paintCursor);
        }

        // Legend overlay at top
        float legendY = 36.0f;

        // Original Indicator (Cyan)
        paintLegend.setColor(Color.parseColor("#00E5FF"));
        canvas.drawCircle(30, legendY - 8, 8, paintLegend);
        paintLegend.setColor(Color.parseColor("#CBD5E1"));
        canvas.drawText("Real Audio (Mic / Input)", 48, legendY, paintLegend);

        // Filtered Indicator (Amber)
        float secondColX = w / 2.0f + 20;
        paintLegend.setColor(Color.parseColor("#FFD600"));
        canvas.drawCircle(secondColX, legendY - 8, 8, paintLegend);
        paintLegend.setColor(Color.parseColor("#CBD5E1"));
        canvas.drawText("After Model (Filtered)", secondColX + 18, legendY, paintLegend);
    }
}
