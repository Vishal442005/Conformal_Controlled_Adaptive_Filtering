package com.research.ccaf.ui;

import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.RadioButton;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.research.ccaf.R;
import com.research.ccaf.dsp.ModelInfo;
import com.research.ccaf.dsp.ModelManager;

import java.util.List;

/**
 * RecyclerView adapter displaying all research models and custom imported models.
 */
public class ModelAdapter extends RecyclerView.Adapter<ModelAdapter.ModelViewHolder> {

    public interface OnModelSelectedCallback {
        void onSelected(ModelInfo model);
    }

    private final List<ModelInfo> models;
    private final OnModelSelectedCallback callback;

    public ModelAdapter(List<ModelInfo> models, OnModelSelectedCallback callback) {
        this.models = models;
        this.callback = callback;
    }

    @NonNull
    @Override
    public ModelViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_model_card, parent, false);
        return new ModelViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ModelViewHolder holder, int position) {
        ModelInfo model = models.get(position);
        ModelInfo active = ModelManager.getInstance().getActiveModelInfo();
        boolean isSelected = (active != null && active.getId().equals(model.getId()));

        holder.tvModelName.setText(model.getName());
        holder.tvModelCategory.setText(model.getCategory());
        holder.tvModelDescription.setText(model.getDescription());
        holder.rbSelect.setChecked(isSelected);

        // Highlight proposed model
        if (model.isProposed()) {
            holder.itemView.setBackgroundResource(R.drawable.bg_proposed_model_card);
            holder.tvModelCategory.setTextColor(Color.parseColor("#10B981")); // Emerald
            holder.tvModelName.setTextColor(Color.parseColor("#34D399"));
        } else {
            holder.itemView.setBackgroundResource(R.drawable.bg_standard_model_card);
            holder.tvModelCategory.setTextColor(Color.parseColor("#94A3B8"));
            holder.tvModelName.setTextColor(Color.WHITE);
        }

        View.OnClickListener clickListener = v -> {
            callback.onSelected(model);
            notifyDataSetChanged();
        };

        holder.itemView.setOnClickListener(clickListener);
        holder.rbSelect.setOnClickListener(clickListener);
    }

    @Override
    public int getItemCount() {
        return models.size();
    }

    static class ModelViewHolder extends RecyclerView.ViewHolder {
        final TextView tvModelName;
        final TextView tvModelCategory;
        final TextView tvModelDescription;
        final RadioButton rbSelect;

        ModelViewHolder(@NonNull View itemView) {
            super(itemView);
            tvModelName = itemView.findViewById(R.id.tvCardModelName);
            tvModelCategory = itemView.findViewById(R.id.tvCardModelCategory);
            tvModelDescription = itemView.findViewById(R.id.tvCardModelDescription);
            rbSelect = itemView.findViewById(R.id.rbCardSelect);
        }
    }
}
